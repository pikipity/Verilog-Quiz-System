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

_BEHAVIORAL_HINT = "RTL view only works for synthesizable code (no #delays, initial blocks, etc.). Simulation waveform is unaffected."


def generate_rtl(week, qid):
    """运行 yosys 生成网表 JSON；失败时返回 yosys 原始错误输出。"""
    settings = settings_service.load_settings()
    runner = ToolRunner('yosys', ['-V'], settings["tool_paths"].get("yosys", ""))
    if not runner.available:
        return {"ok": False, "error": "Yosys not detected. Install it per the manual, or set its path in Settings."}

    code_file = os.path.join(config.SUBMISSIONS_DIR, f"week{week}", qid, f"{qid}.v")
    if not os.path.exists(code_file):
        return {"ok": False, "error": "Write and save your code first."}
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
            "error": (stderr or stdout or "Yosys execution failed").strip(),
            "hint": _BEHAVIORAL_HINT,
        }

    json_path = os.path.join(work_dir, "rtl.json")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            netlist = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"ok": False, "error": "Failed to parse Yosys output."}

    return {"ok": True, "netlist": netlist}
