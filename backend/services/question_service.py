"""
答题服务：题面加载、代码保存、仿真测试、进度管理、GTKWave 拉起
"""
import base64
import json
import os
import re
import shutil
import subprocess
from datetime import datetime

import config
from core import question_manager as qm
from core.code_executor import CodeExecutor
from backend.services import settings_service

_DEFAULT_CODE = "// 在此编写你的 Verilog 代码\n"


def _week_str(week) -> str:
    return f"week{week}"


def _question_dir(week, qid) -> str:
    return os.path.join(config.QUESTIONS_DIR, _week_str(week), qid)


def _submission_dir(week, qid) -> str:
    return os.path.join(config.SUBMISSIONS_DIR, _week_str(week), qid)


# ---------- 题面 ----------

def _embed_images(markdown: str, q_dir: str) -> str:
    """把题面中的相对路径图片替换为 base64 data URI。"""
    def repl(m):
        alt, path = m.group(1), m.group(2)
        if path.startswith(('http://', 'https://', 'data:')):
            return m.group(0)
        img_path = os.path.join(q_dir, path)
        if not os.path.isfile(img_path):
            return m.group(0)
        ext = os.path.splitext(img_path)[1].lstrip('.').lower() or 'png'
        mime = 'jpeg' if ext in ('jpg', 'jpeg') else ext
        try:
            with open(img_path, 'rb') as f:
                data = base64.b64encode(f.read()).decode('ascii')
        except OSError:
            return m.group(0)
        return f'![{alt}](data:image/{mime};base64,{data})'

    return re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', repl, markdown)


def get_question(week, qid):
    """题面（图片base64内嵌）+ testbench。"""
    q_dir = _question_dir(week, qid)
    if not os.path.isdir(q_dir):
        return None

    markdown = ""
    md_path = os.path.join(q_dir, "question.md")
    if os.path.exists(md_path):
        with open(md_path, 'r', encoding='utf-8') as f:
            markdown = _embed_images(f.read(), q_dir)

    testbench = ""
    tb_path = os.path.join(q_dir, "testbench.v")
    if os.path.exists(tb_path):
        with open(tb_path, 'r', encoding='utf-8') as f:
            testbench = f.read()

    info = qm.get_question_info(week, qid) or {}
    return {
        "id": qid,
        "title": info.get("title", ""),
        "markdown": markdown,
        "testbench": testbench,
    }


# ---------- 代码与进度 ----------

def get_code(week, qid):
    code_file = os.path.join(_submission_dir(week, qid), f"{qid}.v")
    code = _DEFAULT_CODE
    if os.path.exists(code_file):
        with open(code_file, 'r', encoding='utf-8') as f:
            code = f.read()
    return {"code": code}


def save_code(week, qid, code: str):
    sub_dir = _submission_dir(week, qid)
    os.makedirs(sub_dir, exist_ok=True)
    with open(os.path.join(sub_dir, f"{qid}.v"), 'w', encoding='utf-8', newline='\n') as f:
        f.write(code)
    _update_progress(week, qid)
    return {"saved": True, "time": datetime.now().strftime("%H:%M:%S")}


def _update_progress(week, qid, completed=None):
    sub_dir = _submission_dir(week, qid)
    os.makedirs(sub_dir, exist_ok=True)
    prog_file = os.path.join(sub_dir, "progress.json")
    prog = qm.read_json(prog_file, {}) or {}
    if completed is not None:
        prog["completed"] = bool(completed)
    prog["last_saved"] = datetime.now().isoformat()
    with open(prog_file, 'w', encoding='utf-8') as f:
        json.dump(prog, f, ensure_ascii=False, indent=2)
    _update_week_progress(week)


def _update_week_progress(week):
    """周级进度汇总 submissions/weekN/progress.json。"""
    week_str = _week_str(week)
    draw = qm.read_json(os.path.join(config.QUESTIONS_DIR, week_str, "draw_result.json"), {}) or {}
    drawn = draw.get("drawn_questions", [])
    completed = 0
    for q in drawn:
        prog = qm.read_json(os.path.join(
            config.SUBMISSIONS_DIR, week_str, q.get("id", ""), "progress.json"), {}) or {}
        if prog.get("completed"):
            completed += 1
    week_prog = {
        "week": int(week),
        "total": len(drawn),
        "completed": completed,
        "updated_at": datetime.now().isoformat(),
    }
    week_dir = os.path.join(config.SUBMISSIONS_DIR, week_str)
    os.makedirs(week_dir, exist_ok=True)
    with open(os.path.join(week_dir, "progress.json"), 'w', encoding='utf-8') as f:
        json.dump(week_prog, f, ensure_ascii=False, indent=2)


def set_completed(week, qid):
    _update_progress(week, qid, completed=True)
    return {"completed": True}


# ---------- 仿真测试 ----------

def _rename_dumpfile(testbench: str, vcd_name: str) -> str:
    """把 testbench 中的 $dumpfile 改为指定文件名。"""
    return re.sub(r'\$dumpfile\("[^"]*"\)', f'$dumpfile("{vcd_name}")', testbench)


def run_test(week, qid, code: str):
    """保存代码 → 分别编译运行学生/参考代码 → 写 result.json。"""
    save_code(week, qid, code)

    settings = settings_service.load_settings()
    executor = CodeExecutor(settings["tool_paths"].get("iverilog", ""))
    if not executor.available:
        return {"ok": False, "error": "未检测到 iverilog。请按安装手册安装，或在设置页手动指定路径。"}

    ref_code = qm.get_reference_code(week, qid)
    if ref_code is None:
        return {"ok": False, "error": "参考代码缺失，请重新同步题目。"}

    tb_path = os.path.join(_question_dir(week, qid), "testbench.v")
    if not os.path.exists(tb_path):
        return {"ok": False, "error": "testbench 缺失，请重新同步题目。"}
    with open(tb_path, 'r', encoding='utf-8') as f:
        testbench = f.read()

    # 临时仿真目录（每次重建）
    temp_dir = os.path.join(_submission_dir(week, qid), "temp")
    shutil.rmtree(temp_dir, ignore_errors=True)
    os.makedirs(temp_dir, exist_ok=True)

    def write_temp(name, content):
        with open(os.path.join(temp_dir, name), 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)

    # 学生代码
    write_temp("student.v", code)
    write_temp("tb_student.v", _rename_dumpfile(testbench, "student_wave.vcd"))
    student = executor.execute(["student.v", "tb_student.v"], temp_dir, "student.vvp")

    # 参考代码（临时解密，编译后立即删除明文）
    write_temp("ref.v", ref_code)
    write_temp("tb_ref.v", _rename_dumpfile(testbench, "ref_wave.vcd"))
    reference = executor.execute(["ref.v", "tb_ref.v"], temp_dir, "ref.vvp")
    try:
        os.remove(os.path.join(temp_dir, "ref.v"))
    except OSError:
        pass
    ref_code = None  # 清除内存中的明文

    result = {
        "compile_success": student.compile_success,
        "run_success": student.run_success,
        "output": student.output,
        "error": student.error,
        "ref_run_success": reference.run_success,
        "ref_output": reference.output if reference.run_success else "",
        "time": datetime.now().isoformat(),
    }

    with open(os.path.join(_submission_dir(week, qid), "result.json"), 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return {"ok": True, "result": result}


def get_result(week, qid):
    return qm.read_json(os.path.join(_submission_dir(week, qid), "result.json"))


# ---------- GTKWave ----------

def open_gtkwave(week, qid, which: str):
    """拉起 GTKWave 查看波形。which: student | ref"""
    vcd_name = "student_wave.vcd" if which == "student" else "ref_wave.vcd"
    label = "你的波形" if which == "student" else "期望波形"
    vcd_path = os.path.join(_submission_dir(week, qid), "temp", vcd_name)

    if not os.path.exists(vcd_path):
        return {"ok": False, "error": f"{label}文件不存在，请先运行测试。"}

    # 用户手动指定的 GTKWave 优先
    settings = settings_service.load_settings()
    override = settings["tool_paths"].get("gtkwave", "")
    if override and os.path.exists(override):
        try:
            subprocess.Popen([override, vcd_path],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"ok": True, "message": f"正在打开{label}…"}
        except Exception as e:
            return {"ok": False, "error": f"GTKWave 启动失败: {e}"}

    from core import gtkwave_helper
    success, message = gtkwave_helper.open_vcd_in_gtkwave(vcd_path, label)
    return {"ok": success, "message" if success else "error": message}
