"""
代码执行器 v2 - iverilog/vvp 跨平台调用

- 支持设置页指定的 iverilog 路径覆盖
- Windows 优先原生调用，失败自动 fallback 到 WSL（含路径转换）
- GTKWave/Yosys 检测不在这里（分别在 gtkwave_helper / yosys_service）
"""
import os
import subprocess
import platform
from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass
class ExecutionResult:
    success: bool
    output: str
    error: str
    compile_success: bool = False
    run_success: bool = False


class CodeExecutor:
    def __init__(self, override_path: str = ''):
        self.system = platform.system()
        self.use_wsl = False
        self.iverilog: Optional[str] = None
        self._detect(override_path)

    @property
    def available(self) -> bool:
        return self.iverilog is not None

    def _detect(self, override_path: str):
        # 1. 用户手动指定的路径
        if override_path and os.path.exists(override_path):
            self.iverilog = override_path
            return

        # 2. 系统 PATH
        try:
            subprocess.run(['iverilog', '-V'], capture_output=True, check=True)
            self.iverilog = 'iverilog'
            return
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # 3. Windows → WSL fallback
        if self.system == 'Windows':
            try:
                subprocess.run(['wsl', 'iverilog', '-V'], capture_output=True, check=True)
                self.use_wsl = True
                self.iverilog = 'iverilog'
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass

    def _to_wsl_path(self, path: str) -> str:
        """C:/Users/x -> /mnt/c/Users/x"""
        if not path or path.startswith('/'):
            return path
        if len(path) >= 2 and path[1] == ':':
            drive = path[0].lower()
            rest = path[2:].replace('\\', '/')
            return f"/mnt/{drive}{rest}"
        return path.replace('\\', '/')

    def _run(self, cmd: List[str], cwd: str = None, timeout: int = 30) -> Tuple[bool, str, str]:
        try:
            if self.use_wsl:
                # 相对路径不需要转换（wsl 会把 cwd 映射到 /mnt/...）；
                # 只转换存在的绝对路径参数
                cmd = [
                    self._to_wsl_path(arg) if os.path.isabs(arg) and os.path.exists(arg) else arg
                    for arg in cmd
                ]
                cmd = ['wsl'] + cmd

            result = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True,
                timeout=timeout, encoding='utf-8', errors='ignore'
            )
            return result.returncode == 0, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            return False, "", "执行超时"
        except Exception as e:
            return False, "", str(e)

    def execute(self, verilog_files: List[str], work_dir: str, vvp_name: str = "out.vvp") -> ExecutionResult:
        """编译 + 运行。verilog_files 与 vvp_name 使用相对 work_dir 的文件名。"""
        compile_ok, stdout, stderr = self._run(
            ['iverilog', '-o', vvp_name] + verilog_files, cwd=work_dir
        )
        if not compile_ok:
            return ExecutionResult(
                success=False, output="",
                error=f"编译失败:\n{stderr or stdout}",
                compile_success=False, run_success=False,
            )

        run_ok, run_out, run_err = self._run(['vvp', vvp_name], cwd=work_dir)

        full_error = ""
        if run_err:
            full_error += run_err + "\n"
        if not run_ok and not run_err:
            full_error = "仿真执行失败"

        return ExecutionResult(
            success=run_ok,
            output=run_out,
            error=full_error.strip(),
            compile_success=True,
            run_success=run_ok,
        )
