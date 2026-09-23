"""
题目对账同步（v2 核心逻辑）

安全原则（AGENTS.md）：
- manifest 拉取失败或 schema 非法 → 中止同步，不删任何本地数据；
- 只有 manifest 校验通过后，才执行"本地有而服务器无"的删除。
"""
import os
import re
import shutil

import config
from core import question_manager as qm
from backend.services import settings_service

SUPPORTED_SCHEMA_VERSION = 2


def _validate_manifest(manifest) -> bool:
    if not isinstance(manifest, dict):
        return False
    if manifest.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        return False
    weeks = manifest.get("weeks")
    if not isinstance(weeks, list):
        return False
    return all(isinstance(w, str) and re.fullmatch(r'week\d+', w) for w in weeks)


def check_server() -> dict:
    """连接测试：只拉取并校验 manifest，不触碰本地数据。"""
    try:
        manifest = qm.fetch_json(f"{config.get_server_url()}/manifest.json")
    except Exception:
        return {"ok": False, "error": "无法连接题目服务器"}
    if not _validate_manifest(manifest):
        return {"ok": False, "error": "题目清单格式不兼容（需要 schema_version: 2），请联系老师更新"}
    return {"ok": True, "weeks": len(manifest["weeks"])}


def run_sync() -> dict:
    """
    对账同步：
    1. 校验 manifest（失败则中止，不删任何数据）
    2. 删除服务器上已消失的 week（questions/submissions/reports 一并删除）
    3. 新增/更新 week：下载 info.json、学号抽题、下载加密
    返回变更摘要。
    """
    settings = settings_service.load_settings()
    student_id = settings.get("student_id", "").strip()
    if not student_id:
        return {"ok": False, "need_settings": True, "error": "请先在设置页填写学号"}

    base = config.get_server_url()
    try:
        manifest = qm.fetch_json(f"{base}/manifest.json")
    except Exception:
        return {"ok": False, "error": "无法连接题目服务器，本地数据未做任何改动"}

    if not _validate_manifest(manifest):
        return {"ok": False, "error": "题目清单格式不兼容（缺少或不支持的 schema_version），已中止同步，本地数据未改动"}

    server_weeks = {int(w[4:]) for w in manifest["weeks"]}
    local_weeks = qm.scan_local_weeks()
    summary = {"added": [], "updated": [], "removed": [], "errors": []}

    # 删除消失的 week
    for w in sorted(local_weeks - server_weeks):
        shutil.rmtree(os.path.join(config.QUESTIONS_DIR, f"week{w}"), ignore_errors=True)
        shutil.rmtree(os.path.join(config.SUBMISSIONS_DIR, f"week{w}"), ignore_errors=True)
        report = os.path.join(config.REPORTS_DIR, f"week{w}_report.md")
        if os.path.exists(report):
            try:
                os.remove(report)
            except OSError:
                pass
        summary["removed"].append(w)

    # 新增 / 更新
    for w in sorted(server_weeks):
        try:
            info = qm.fetch_json(f"{base}/week{w}/info.json")
        except Exception:
            summary["errors"].append(f"week{w}: 获取配置失败")
            continue

        local_info = qm.read_json(os.path.join(config.QUESTIONS_DIR, f"week{w}", "info.json"))
        if local_info and local_info.get("updated_at", "") >= info.get("updated_at", ""):
            continue

        try:
            qm.download_week(w, info, student_id)
        except Exception:
            summary["errors"].append(f"week{w}: 题目下载失败")
            continue

        summary["updated" if w in local_weeks else "added"].append(w)

    return {"ok": True, "summary": summary}


def list_weeks() -> list:
    """周次列表（含进度）。"""
    result = []
    for w in sorted(qm.scan_local_weeks()):
        week_str = f"week{w}"
        info = qm.read_json(os.path.join(config.QUESTIONS_DIR, week_str, "info.json"), {}) or {}
        draw = qm.read_json(os.path.join(config.QUESTIONS_DIR, week_str, "draw_result.json"), {}) or {}
        drawn = draw.get("drawn_questions", [])

        completed = 0
        for q in drawn:
            prog = qm.read_json(os.path.join(
                config.SUBMISSIONS_DIR, week_str, q.get("id", ""), "progress.json"))
            if prog and prog.get("completed"):
                completed += 1

        result.append({
            "week": w,
            "title": info.get("title", f"Week {w}"),
            "total": len(drawn),
            "completed": completed,
        })
    return result


def list_questions(week: int):
    """某周抽中题目列表（含完成状态）。"""
    week_str = f"week{week}"
    draw = qm.read_json(os.path.join(config.QUESTIONS_DIR, week_str, "draw_result.json"))
    if not draw:
        return None

    questions = []
    for q in draw.get("drawn_questions", []):
        qid = q.get("id", "")
        prog = qm.read_json(os.path.join(
            config.SUBMISSIONS_DIR, week_str, qid, "progress.json"), {}) or {}
        questions.append({
            "id": qid,
            "title": q.get("title", ""),
            "completed": bool(prog.get("completed")),
        })
    return questions
