"""
诊断服务：四工具的三级探测 + 三级验证 + 功能自检

三级验证（AGENTS.md）：
1. 存在性：手动路径 → PATH → 常见安装目录 → WSL
2. 版本：解析版本号并与锁定版本比对（绿=匹配，黄=不匹配但可用，红=未找到）
3. 功能自检：内置最小样例真实跑通（iverilog 编译+vvp 仿真、yosys JSON 生成）；
   GTKWave 无法无头验证，提供测试打开按钮。
"""
import json
import os
import platform
import re
import shutil
import subprocess

import config
from core.tool_runner import ToolRunner, popen_kwargs
from core.code_executor import CodeExecutor
from backend.services import settings_service

_COMMON_PATHS = {
    "iverilog": [
        r"C:\iverilog\bin\iverilog.exe",
    ],
    "gtkwave": [
        r"C:\Program Files\GTKWave\bin\gtkwave.exe",
        r"C:\Program Files (x86)\GTKWave\bin\gtkwave.exe",
    ],
    "yosys": [
        r"C:\oss-cad-suite\bin\yosys.exe",
    ],
}

_TOOLS = [
    {"name": "iverilog", "display": "Icarus Verilog", "version_args": ["-V"]},
    {"name": "gtkwave", "display": "GTKWave", "version_args": ["--version"]},
    {"name": "yosys", "display": "Yosys", "version_args": ["-V"]},
]

_VERSION_RE = r'(\d+\.\d+(?:\.\d+)?)'

# 自检用的最小样例（与题目数据无关，首次启动即可运行）
_SELF_DESIGN = "module selfcheck(input a, input b, output y);\n    assign y = a & b;\nendmodule\n"
_SELF_TB = """`timescale 1ns/1ps
module tb_selfcheck;
    reg a, b;
    wire y;
    selfcheck dut(.a(a), .b(b), .y(y));
    initial begin
        a=0; b=0; #1 $display("SC y=%b", y);
        a=1; b=1; #1 $display("SC y=%b", y);
        $finish;
    end
endmodule
"""


def _make_runner(name: str, version_args: list, override: str) -> ToolRunner:
    """探测顺序：手动路径 → 常见安装目录 → PATH → WSL。"""
    if not (override and os.path.exists(override)) and os.name == 'nt':
        for path in _COMMON_PATHS.get(name, []):
            if os.path.exists(path):
                override = path
                break
    return ToolRunner(name, version_args, override)


def _parse_version(raw: str) -> str:
    m = re.search(_VERSION_RE, raw or "")
    return m.group(1) if m else ""


def _tool_entry(tool: dict, override: str) -> dict:
    name = tool["name"]
    runner = _make_runner(name, tool["version_args"], override)
    pinned = config.PINNED_VERSIONS.get(name, "")

    entry = {
        "name": name,
        "display": tool["display"],
        "found": runner.available,
        "mode": None,
        "path": "",
        "version": "",
        "pinned": pinned,
        "status": "red",
    }
    if not runner.available:
        return entry

    if runner.use_wsl:
        entry["mode"] = "wsl"
        entry["path"] = f"wsl: {name}"
    elif override and runner.exe == override:
        entry["mode"] = "override"
        entry["path"] = override
    else:
        entry["mode"] = "native"
        entry["path"] = f"PATH: {name}"

    raw = runner.get_version()
    entry["version_raw"] = raw
    detected = _parse_version(raw)
    entry["version"] = detected

    if pinned and detected and detected.startswith(pinned):
        entry["status"] = "green"
    else:
        entry["status"] = "yellow"
    return entry


def get_tools_status() -> dict:
    settings = settings_service.load_settings()
    overrides = settings.get("tool_paths", {})
    tools = [_tool_entry(t, overrides.get(t["name"], "")) for t in _TOOLS]
    return {
        "app_version": config.VERSION,
        "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "python": platform.python_version(),
        "data_dir": config.BASE_DIR,
        "tools": tools,
    }


def run_selfcheck() -> dict:
    """用内置最小样例真实验证 iverilog 编译+vvp 仿真、yosys JSON 生成。"""
    settings = settings_service.load_settings()
    overrides = settings.get("tool_paths", {})
    work_dir = os.path.join(config.BASE_DIR, "temp_selfcheck")
    shutil.rmtree(work_dir, ignore_errors=True)
    os.makedirs(work_dir, exist_ok=True)

    def write_temp(name, content):
        with open(os.path.join(work_dir, name), 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)

    write_temp("selfcheck.v", _SELF_DESIGN)
    write_temp("tb_selfcheck.v", _SELF_TB)

    checks = []

    # 1. iverilog 编译 + vvp 仿真
    executor = CodeExecutor(overrides.get("iverilog", ""))
    if not executor.available:
        checks.append({"name": "iverilog compile + simulate", "ok": False, "detail": "iverilog not detected"})
    else:
        result = executor.execute(["selfcheck.v", "tb_selfcheck.v"], work_dir, "sc.vvp")
        if result.run_success and "SC y=1" in result.output:
            checks.append({"name": "iverilog compile + simulate", "ok": True, "detail": "Compile and simulation passed"})
        else:
            detail = result.error or result.output or "Unexpected simulation output"
            checks.append({"name": "iverilog compile + simulate", "ok": False, "detail": detail[:300]})

    # 2. yosys 网表生成
    yosys = _make_runner("yosys", ["-V"], overrides.get("yosys", ""))
    if not yosys.available:
        checks.append({"name": "yosys netlist generation", "ok": False, "detail": "Yosys not detected"})
    else:
        ok, stdout, stderr = yosys.run(
            ['-p', 'read_verilog selfcheck.v; hierarchy -auto-top; proc; write_json sc.json'],
            cwd=work_dir, timeout=30)
        json_ok = False
        if ok:
            try:
                with open(os.path.join(work_dir, "sc.json"), 'r', encoding='utf-8') as f:
                    json_ok = "selfcheck" in json.load(f).get("modules", {})
            except (OSError, json.JSONDecodeError):
                json_ok = False
        if json_ok:
            checks.append({"name": "yosys netlist generation", "ok": True, "detail": "RTL netlist generation passed"})
        else:
            checks.append({"name": "yosys netlist generation", "ok": False,
                           "detail": (stderr or stdout or "Failed to parse output")[:300]})

    # 3. GTKWave（无法无头验证，只报告探测结果）
    gtk = _tool_entry({"name": "gtkwave", "display": "GTKWave", "version_args": ["--version"]},
                      overrides.get("gtkwave", ""))
    checks.append({
        "name": "GTKWave",
        "ok": gtk["found"],
        "detail": "Found. Click 'Test-launch GTKWave' to confirm the window opens." if gtk["found"] else "GTKWave not found",
    })

    return {"ok": all(c["ok"] for c in checks), "checks": checks}


def test_open_gtkwave() -> dict:
    """测试打开 GTKWave（无文件，供学生目视确认）。"""
    settings = settings_service.load_settings()
    override = settings.get("tool_paths", {}).get("gtkwave", "")
    runner = _make_runner("gtkwave", ["--version"], override)
    if not runner.available:
        return {"ok": False, "error": "GTKWave not detected. Install it per the manual, or set its path in Settings."}

    try:
        if runner.use_wsl:
            subprocess.Popen(['wsl', 'DISPLAY=:0', 'gtkwave'], **popen_kwargs())
        else:
            subprocess.Popen([runner.exe], **popen_kwargs())
        return {"ok": True, "message": "GTKWave launch attempted — please confirm the window opened."}
    except Exception as e:
        return {"ok": False, "error": f"Launch failed: {e}"}
