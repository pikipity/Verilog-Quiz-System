"""
代码执行器 - 调用iverilog进行编译和仿真
"""
import os
import re
import subprocess
import platform
from pathlib import Path
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    output: str
    error: str
    vcd_file: Optional[str] = None
    compile_success: bool = False
    run_success: bool = False


class CodeExecutor:
    """
    代码执行器
    
    支持跨平台调用iverilog：
    - Linux/Mac: 直接调用iverilog
    - Windows: 先尝试直接调用，失败则尝试WSL
    """
    
    def __init__(self):
        self.system = platform.system()
        self.use_wsl = False
        self._detect_iverilog()
    
    def _detect_iverilog(self):
        """检测iverilog环境"""
        if self.system in ['Linux', 'Darwin']:
            # Linux/Mac直接检测
            try:
                subprocess.run(['iverilog', '-V'], capture_output=True, check=True)
                print("检测到iverilog (Linux/Mac)")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("警告: 未检测到iverilog，请安装")
        else:
            # Windows: 先尝试直接调用
            try:
                subprocess.run(['iverilog', '-V'], capture_output=True, check=True)
                print("检测到iverilog (Windows)")
            except (subprocess.CalledProcessError, FileNotFoundError):
                # 尝试WSL
                try:
                    subprocess.run(['wsl', 'iverilog', '-V'], capture_output=True, check=True)
                    self.use_wsl = True
                    print("检测到iverilog (WSL)")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    print("警告: 未检测到iverilog (Windows/WSL)")
    
    def _run_command(self, cmd: List[str], cwd: str = None, timeout: int = 30) -> Tuple[bool, str, str]:
        """
        运行命令
        
        Args:
            cmd: 命令列表
            cwd: 工作目录
            timeout: 超时时间（秒）
            
        Returns:
            (是否成功, stdout, stderr)
        """
        try:
            if self.use_wsl:
                # Windows路径转换为WSL路径
                if cwd:
                    cwd = self._to_wsl_path(cwd)
                # 转换命令中的文件路径
                cmd = [self._to_wsl_path(arg) if os.path.exists(arg) or '/' in arg else arg 
                       for arg in cmd]
                cmd = ['wsl'] + cmd
            
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='ignore'
            )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "", "执行超时"
        except Exception as e:
            return False, "", str(e)
    
    def _to_wsl_path(self, path: str) -> str:
        """
        将Windows路径转换为WSL路径
        
        例如: C:/Users/name/file -> /mnt/c/Users/name/file
        """
        if not path or path.startswith('/'):
            return path
        
        # 处理Windows绝对路径
        if len(path) >= 2 and path[1] == ':':
            drive = path[0].lower()
            rest = path[2:].replace('\\', '/')
            return f"/mnt/{drive}{rest}"
        
        # 相对路径
        return path.replace('\\', '/')
    
    def compile(self, verilog_files: List[str], output_file: str, work_dir: str) -> Tuple[bool, str]:
        """
        编译Verilog文件
        
        Args:
            verilog_files: Verilog源文件列表
            output_file: 输出文件名
            work_dir: 工作目录
            
        Returns:
            (是否成功, 错误信息)
        """
        cmd = ['iverilog', '-o', output_file] + verilog_files
        success, stdout, stderr = self._run_command(cmd, cwd=work_dir)
        
        if success:
            return True, ""
        else:
            return False, stderr or stdout
    
    def run_simulation(self, vvp_file: str, work_dir: str) -> Tuple[bool, str, str]:
        """
        运行仿真
        
        Args:
            vvp_file: vvp文件路径
            work_dir: 工作目录
            
        Returns:
            (是否成功, 输出内容, 错误信息)
        """
        cmd = ['vvp', vvp_file]
        success, stdout, stderr = self._run_command(cmd, cwd=work_dir)
        
        return success, stdout, stderr
    
    def execute(self, verilog_files: List[str], work_dir: str, vvp_name: str = "out.vvp") -> ExecutionResult:
        """
        完整执行流程：编译+运行
        
        Args:
            verilog_files: Verilog源文件列表（testbench应在最后）
            work_dir: 工作目录
            vvp_name: 生成的vvp文件名
            
        Returns:
            ExecutionResult
        """
        vvp_path = os.path.join(work_dir, vvp_name)
        
        # 步骤1：编译
        compile_success, compile_error = self.compile(verilog_files, vvp_name, work_dir)
        
        if not compile_success:
            return ExecutionResult(
                success=False,
                output="",
                error=f"编译失败:\n{compile_error}",
                compile_success=False,
                run_success=False
            )
        
        # 步骤2：运行
        run_success, run_output, run_error = self.run_simulation(vvp_name, work_dir)
        
        # 查找VCD文件
        vcd_file = None
        if run_success:
            # 从输出中提取VCD文件名
            vcd_match = re.search(r'\$dumpfile\("(.+?)"\)', ''.join(open(f).read() for f in verilog_files if os.path.exists(f)))
            if vcd_match:
                vcd_name = vcd_match.group(1)
                vcd_path = os.path.join(work_dir, vcd_name)
                if os.path.exists(vcd_path):
                    vcd_file = vcd_path
        
        # 合并错误信息
        full_error = ""
        if run_error:
            full_error += run_error + "\n"
        if not run_success and not run_error:
            full_error = "仿真运行失败"
        
        return ExecutionResult(
            success=compile_success and run_success,
            output=run_output,
            error=full_error.strip(),
            vcd_file=vcd_file,
            compile_success=compile_success,
            run_success=run_success
        )
    
    def extract_display_values(self, output: str) -> List[Dict]:
        """
        从$display输出中提取数值
        
        期望格式: "time=10 a=1 b=0 sel=0 out=1"
        
        Args:
            output: 仿真输出
            
        Returns:
            数值列表，每项是字典
        """
        values = []
        
        # 匹配键值对格式
        pattern = r'time=(\d+)\s+(.+)'
        
        for line in output.split('\n'):
            line = line.strip()
            match = re.match(pattern, line)
            if match:
                time_val = int(match.group(1))
                rest = match.group(2)
                
                # 解析其余键值对
                entry = {'time': time_val}
                kv_pattern = r'(\w+)=([\w\'b\d]+)'
                for kv_match in re.finditer(kv_pattern, rest):
                    key = kv_match.group(1)
                    val = kv_match.group(2)
                    entry[key] = val
                
                values.append(entry)
        
        return values


# 单例实例
code_executor = CodeExecutor()
