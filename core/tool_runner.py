"""
跨平台命令执行器：手动路径 → PATH → WSL fallback（Windows）

关键工程细节（勿删）：
- 所有子进程必须 stdin=DEVNULL + CREATE_NO_WINDOW(Windows)：
  打包后为 windowed 程序（无控制台），子进程若继承无效 stdin 句柄，
  wsl.exe 等控制台程序会间歇性报 0xc0000142（DLL 初始化失败）；
  CREATE_NO_WINDOW 同时消除每次调用闪黑窗的问题。
- 进程启动类错误（0xc0000142 等）自动重试一次。
"""
import os
import platform
import subprocess
import time
from typing import List, Optional, Tuple

# 0xc0000142 (STATUS_DLL_INIT_FAILED) 的有符号返回码
_DLL_INIT_FAILED = -1073741502


def _quiet_kwargs() -> dict:
    """windowed 程序必需的子进程静默参数。"""
    kwargs = {"stdin": subprocess.DEVNULL}
    if platform.system() == 'Windows':
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    return kwargs


def popen_kwargs() -> dict:
    """后台启动（GUI 工具）用的参数：静默 + 无窗 + 独立进程组。"""
    kwargs = {
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if platform.system() == 'Windows':
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
    return kwargs


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
        if self._try_invoke([self.exe_name] + self.version_args):
            self.exe = self.exe_name
            return

        # 3. Windows → WSL fallback
        if self.system == 'Windows':
            if self._try_invoke(['wsl', self.exe_name] + self.version_args):
                self.use_wsl = True
                self.exe = self.exe_name

    def _try_invoke(self, cmd: List[str]) -> bool:
        """检测命令可执行（启动类错误重试一次）。"""
        for attempt in range(2):
            try:
                result = subprocess.run(cmd, capture_output=True, check=False,
                                        timeout=10, **_quiet_kwargs())
                if result.returncode == _DLL_INIT_FAILED and attempt == 0:
                    time.sleep(0.5)
                    continue
                return result.returncode == 0
            except (subprocess.TimeoutExpired, OSError):
                if attempt == 0:
                    time.sleep(0.5)
        return False

    def _to_wsl_path(self, path: str) -> str:
        if not path or path.startswith('/'):
            return path
        if len(path) >= 2 and path[1] == ':':
            drive = path[0].lower()
            rest = path[2:].replace('\\', '/')
            return f"/mnt/{drive}{rest}"
        return path.replace('\\', '/')

    def _resolve_program(self, program: Optional[str]) -> str:
        """伴随程序（如 vvp 随 iverilog）：绝对路径时取同目录同名程序。"""
        if program is None or program == self.exe_name:
            return self.exe
        if os.path.isabs(self.exe):
            suffix = '.exe' if os.name == 'nt' and '.' not in program else ''
            return os.path.join(os.path.dirname(self.exe), program + suffix)
        return program

    def run(self, args: List[str], program: str = None, cwd: str = None,
            timeout: int = 30, retries: int = 1) -> Tuple[bool, str, str]:
        prog = self._resolve_program(program)
        if self.use_wsl:
            cmd = ['wsl', prog] + [
                self._to_wsl_path(a) if os.path.isabs(a) and os.path.exists(a) else a
                for a in args
            ]
        else:
            cmd = [prog] + list(args)

        for attempt in range(retries + 1):
            try:
                result = subprocess.run(
                    cmd, cwd=cwd, capture_output=True, text=True,
                    timeout=timeout, encoding='utf-8', errors='ignore',
                    **_quiet_kwargs()
                )
                if result.returncode == _DLL_INIT_FAILED and attempt < retries:
                    time.sleep(0.5)
                    continue
                return result.returncode == 0, result.stdout, result.stderr

            except subprocess.TimeoutExpired:
                return False, "", "Execution timed out"
            except OSError as e:
                if attempt < retries:
                    time.sleep(0.5)
                    continue
                return False, "", str(e)

        return False, "", "Process launch failed"

    def get_version(self) -> str:
        """返回版本输出的第一行；不可用返回空串。"""
        ok, out, err = self.run(self.version_args, timeout=10)
        text = (out or err or '').strip()
        return text.split('\n')[0].strip() if text else ''
