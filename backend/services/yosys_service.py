"""
Yosys 服务：对学生代码生成 RTL 视图数据

约束（AGENTS.md）：仅学生代码，不生成参考代码的 RTL 视图。
"""
import json
import os
import shutil

import config
from core.tool_runner import ToolRunner
from backend.services import settings_service

_YOSYS_SCRIPT = 'read_verilog student.v; hierarchy -auto-top; proc; opt; write_json rtl.json'

_BEHAVIORAL_HINT = "RTL 视图仅适用于可综合代码（不包含 #延迟、initial 等行为级语法），仿真波形不受影响。"


def generate_rtl(week, qid):
    """运行 yosys 生成网表 JSON；失败时返回 yosys 原始错误输出。"""
    settings = settings_service.load_settings()
    runner = ToolRunner('yosys', ['-V'], settings["tool_paths"].get("yosys", ""))
    if not runner.available:
        return {"ok": False, "error": "未检测到 Yosys。请按安装手册安装，或在设置页手动指定路径。"}

    code_file = os.path.join(config.SUBMISSIONS_DIR, f"week{week}", qid, f"{qid}.v")
    if not os.path.exists(code_file):
        return {"ok": False, "error": "请先编写并保存代码。"}
    with open(code_file, 'r', encoding='utf-8') as f:
        code = f.read()

    work_dir = os.path.join(config.SUBMISSIONS_DIR, f"week{week}", qid, "temp_rtl")
    shutil.rmtree(work_dir, ignore_errors=True)
    os.makedirs(work_dir, exist_ok=True)
    with open(os.path.join(work_dir, "student.v"), 'w', encoding='utf-8', newline='\n') as f:
        f.write(code)

    ok, stdout, stderr = runner.run(['-p', _YOSYS_SCRIPT], cwd=work_dir, timeout=30)
    if not ok:
        return {
            "ok": False,
            "error": (stderr or stdout or "Yosys 执行失败").strip(),
            "hint": _BEHAVIORAL_HINT,
        }

    json_path = os.path.join(work_dir, "rtl.json")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            netlist = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"ok": False, "error": "Yosys 输出解析失败。"}

    return {"ok": True, "netlist": netlist}
