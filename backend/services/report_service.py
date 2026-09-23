"""
报告服务：生成、读取、打开文件位置
"""
import os
import subprocess
import sys

import config
from core.report_generator import report_generator
from backend.services import settings_service


def generate_report(week: int) -> dict:
    settings = settings_service.load_settings()
    path = report_generator.generate_week_report(week, {
        "student_id": settings.get("student_id", ""),
        "name": settings.get("name", ""),
    })
    if not path:
        return {"ok": False, "error": "生成失败：本周题目数据缺失，请先同步。"}
    return {"ok": True, "filename": os.path.basename(path)}


def get_report(week: int) -> dict:
    path = os.path.join(config.REPORTS_DIR, f"week{week}_report.md")
    if not os.path.exists(path):
        return {"exists": False}
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return {"exists": True, "filename": os.path.basename(path), "content": content}


def open_reports_folder() -> dict:
    """在系统文件管理器中打开报告目录。"""
    folder = config.REPORTS_DIR
    try:
        if sys.platform == 'win32':
            os.startfile(folder)
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', folder])
        else:
            subprocess.Popen(['xdg-open', folder],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
