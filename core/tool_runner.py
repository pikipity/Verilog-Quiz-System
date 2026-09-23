"""
跨平台命令执行器：手动路径 → PATH → WSL fallback（Windows）

供 Yosys、诊断等需要调用外部工具的服务使用。
（iverilog 的执行封装在 core/code_executor.py，含编译+仿真流程。）
"""
import os
import platform
import subprocess
from typing import List, Optional, Tuple


class ToolRunner:
    def __init__(self, exe_name: str, version_args: List[str] = None, override_path: str = ''):
        self.exe_name = exe_name
        self.version_args = list(version_args) if version_args else ['--version']
        self.system = platform.system()
        self.use_wsl = False
        self.exe: Optional[str] = None
        self._detect(override_path)

    @property
    def available(self) -> bool:
        return self.exe is not None

    def _detect(self, override_path: str):
        # 1. 用户手动指定的路径
        if override_path and os.path.exists(override_path):
            self.exe = override_path
            return

        # 2. 系统 PATH
        try:
            subprocess.run([self.exe_name] + self.version_args,
                           capture_output=True, check=True)
            self.exe = self.exe_name
            return
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # 3. Windows → WSL fallback
        if self.system == 'Windows':
            try:
                subprocess.run(['wsl', self.exe_name] + self.version_args,
                               capture_output=True, check=True)
                self.use_wsl = True
                self.exe = self.exe_name
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass

    def _to_wsl_path(self, path: str) -> str:
        if not path or path.startswith('/'):
            return path
        if len(path) >= 2 and path[1] == ':':
            drive = path[0].lower()
            rest = path[2:].replace('\\', '/')
            return f"/mnt/{drive}{rest}"
        return path.replace('\\', '/')

    def run(self, args: List[str], cwd: str = None, timeout: int = 30) -> Tuple[bool, str, str]:
        cmd = [self.exe] + list(args)
        try:
            if self.use_wsl:
                cmd = ['wsl', self.exe] + [
                    self._to_wsl_path(a) if os.path.isabs(a) and os.path.exists(a) else a
                    for a in args
                ]

            result = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True,
                timeout=timeout, encoding='utf-8', errors='ignore'
            )
            return result.returncode == 0, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            return False, "", "执行超时"
        except Exception as e:
            return False, "", str(e)

    def get_version(self) -> str:
        """返回版本输出的第一行；不可用返回空串。"""
        ok, out, err = self.run(self.version_args, timeout=10)
        text = (out or err or '').strip()
        return text.split('\n')[0].strip() if text else ''
