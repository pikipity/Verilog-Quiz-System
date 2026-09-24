"""
报告与文件位置服务：报告生成/读取、打开报告目录、打开数据目录
"""
import os
import subprocess
import sys

import config
from core.report_generator import report_generator
from core.tool_runner import popen_kwargs
from backend.services import settings_service


def generate_report(week: int) -> dict:
    settings = settings_service.load_settings()
    path = report_generator.generate_week_report(week, {
        "student_id": settings.get("student_id", ""),
        "name": settings.get("name", ""),
    })
    if not path:
        return {"ok": False, "error": "Failed to generate: week data missing. Please sync questions first."}
    return {"ok": True, "filename": os.path.basename(path)}


def get_report(week: int) -> dict:
    path = os.path.join(config.REPORTS_DIR, f"week{week}_report.md")
    if not os.path.exists(path):
        return {"exists": False}
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return {"exists": True, "filename": os.path.basename(path), "content": content}


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
