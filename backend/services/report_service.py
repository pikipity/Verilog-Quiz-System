"""
报告与文件位置服务：PDF 报告生成/读取、打开报告目录、打开数据目录
"""
import os
import subprocess
import sys

import config
from core.report_generator import report_generator
from core.pdf_generator import build_week_pdf
from core.tool_runner import popen_kwargs
from backend.services import settings_service


def _report_path(week: int) -> str:
    return os.path.join(config.REPORTS_DIR, f"week{week}_report.pdf")


def generate_report(week: int) -> dict:
    """生成结构化内容并渲染为 PDF（覆盖旧 PDF）。Markdown 不落盘。"""
    settings = settings_service.load_settings()
    report = report_generator.build_week_report(week, {
        "student_id": settings.get("student_id", ""),
        "name": settings.get("name", ""),
    })
    if not report:
        return {"ok": False, "error": "Failed to generate: week data missing. Please sync questions first."}

    path = _report_path(week)
    try:
        build_week_pdf(report, path)
    except Exception as e:
        return {"ok": False, "error": f"PDF rendering failed: {e}"}
    return {"ok": True, "filename": os.path.basename(path), "size": os.path.getsize(path)}


def get_report(week: int) -> dict:
    """报告存在性与元信息（不含内容）。"""
    path = _report_path(week)
    if not os.path.exists(path):
        return {"exists": False}
    return {
        "exists": True,
        "filename": os.path.basename(path),
        "size": os.path.getsize(path),
        "updated": os.path.getmtime(path),
    }


def get_report_pdf(week: int):
    """返回 PDF 二进制；不存在返回 None。"""
    path = _report_path(week)
    if not os.path.exists(path):
        return None
    with open(path, 'rb') as f:
        return f.read()


def _open_folder(path: str) -> dict:
    """在系统文件管理器中打开指定目录。"""
    try:
        if sys.platform == 'win32':
            os.startfile(path)
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', path], **popen_kwargs())
        else:
            subprocess.Popen(['xdg-open', path], **popen_kwargs())
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def open_reports_folder() -> dict:
    return _open_folder(config.REPORTS_DIR)


def open_data_folder() -> dict:
    return _open_folder(config.BASE_DIR)
