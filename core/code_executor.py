"""
代码执行器 v2 - iverilog/vvp 跨平台调用

- 底层执行统一走 core/tool_runner.ToolRunner（静默参数 + 启动错误重试）
- 支持设置页指定的 iverilog 路径覆盖（vvp 取同目录伴随程序）
- Windows 优先原生调用，失败自动 fallback 到 WSL
"""
from dataclasses import dataclass
from typing import List

from core.tool_runner import ToolRunner


@dataclass
class ExecutionResult:
    success: bool
    output: str
    error: str
    compile_success: bool = False
    run_success: bool = False


class CodeExecutor:
    def __init__(self, override_path: str = ''):
        self._runner = ToolRunner('iverilog', ['-V'], override_path)

    @property
    def available(self) -> bool:
        return self._runner.available

    def execute(self, verilog_files: List[str], work_dir: str, vvp_name: str = "out.vvp") -> ExecutionResult:
        """编译 + 运行。verilog_files 与 vvp_name 使用相对 work_dir 的文件名。"""
        compile_ok, stdout, stderr = self._runner.run(
            ['-o', vvp_name] + verilog_files, cwd=work_dir
        )
        if not compile_ok:
            return ExecutionResult(
                success=False, output="",
                error=f"Compilation failed:\n{stderr or stdout}",
                compile_success=False, run_success=False,
            )

        run_ok, run_out, run_err = self._runner.run([vvp_name], program='vvp', cwd=work_dir)

        full_error = ""
        if run_err:
            full_error += run_err + "\n"
        if not run_ok and not run_err:
            full_error = "Simulation execution failed"

        return ExecutionResult(
            success=run_ok,
            output=run_out,
            error=full_error.strip(),
            compile_success=True,
            run_success=run_ok,
        )
