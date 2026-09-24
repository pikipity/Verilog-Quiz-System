"""
学生设置：学号、姓名、工具路径覆盖。

修改学号的后果（AGENTS.md 约定）：清空 questions/submissions/reports 全部本地数据。
"""
import json
import os
import shutil

import config

_DEFAULT = {
    "student_id": "",
    "name": "",
    "tool_paths": {"iverilog": "", "gtkwave": "", "yosys": ""},
}


def load_settings() -> dict:
    try:
        with open(config.SETTINGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        data = {}

    merged = json.loads(json.dumps(_DEFAULT))
    for key in ("student_id", "name"):
        if isinstance(data.get(key), str):
            merged[key] = data[key]
    if isinstance(data.get("tool_paths"), dict):
        for key in _DEFAULT["tool_paths"]:
            value = data["tool_paths"].get(key)
            if isinstance(value, str):
                merged["tool_paths"][key] = value
    return merged


def save_settings(new: dict) -> dict:
    """保存设置。学号变更时清空本地全部数据（wiped=True）。"""
    old = load_settings()
    old_id = old.get("student_id", "").strip()
    new_id = str(new.get("student_id", "")).strip()

    if not new_id:
        return {"saved": False, "error": "Student ID is required"}
    if '/' in new_id or '\\' in new_id:
        return {"saved": False, "error": "Student ID must not contain path separators"}

    wiped = False
    if old_id and old_id != new_id:
        wipe_local_data()
        wiped = True

    merged = load_settings()
    merged["student_id"] = new_id
    if "name" in new:
        merged["name"] = str(new["name"]).strip()
    tool_paths = new.get("tool_paths")
    if isinstance(tool_paths, dict):
        for key in merged["tool_paths"]:
            if key in tool_paths:
                merged["tool_paths"][key] = str(tool_paths[key]).strip()

    with open(config.SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    return {"saved": True, "wiped": wiped}


def wipe_local_data():
    """清空 questions/submissions/reports 的内容（保留目录本身）。"""
    for directory in (config.QUESTIONS_DIR, config.SUBMISSIONS_DIR, config.REPORTS_DIR):
        if not os.path.isdir(directory):
            continue
        for item in os.listdir(directory):
            path = os.path.join(directory, item)
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            else:
                try:
                    os.remove(path)
                except OSError:
                    pass
