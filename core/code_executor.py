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
    """Execution result"""
    success: bool
    output: str
    error: str
    vcd_file: Optional[str] = None
    compile_success: bool = False
    run_success: bool = False


class CodeExecutor:
    """
    Code Executor
    
    Support cross-platform iverilog calls:
    - Linux/Mac: Call iverilog directly
    - Windows: Try direct call first, then try WSL
    """
    
    def __init__(self):
        self.system = platform.system()
        self.use_wsl = False
        self._detect_iverilog()
    
    def _detect_iverilog(self):
        """Detect iverilog environment"""
        if self.system in ['Linux', 'Darwin']:
            # Linux/Mac direct detection
            try:
                subprocess.run(['iverilog', '-V'], capture_output=True, check=True)
                print("Detected iverilog (Linux/Mac)")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("Warning: iverilog not detected, please install")
        else:
            # Windows: 先尝试直接调用
            try:
                subprocess.run(['iverilog', '-V'], capture_output=True, check=True)
                print("Detected iverilog (Windows)")
            except (subprocess.CalledProcessError, FileNotFoundError):
                # 尝试WSL
                try:
                    subprocess.run(['wsl', 'iverilog', '-V'], capture_output=True, check=True)
                    self.use_wsl = True
                    print("Detected iverilog (WSL)")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    print("Warning: iverilog not detected (Windows/WSL)")
    
    def _run_command(self, cmd: List[str], cwd: str = None, timeout: int = 30) -> Tuple[bool, str, str]:
        """
        Run command
        
        Args:
            cmd: Command list
            cwd: Working directory
            timeout: Timeout (seconds)
            
        Returns:
            (success, stdout, stderr)
        """
        try:
            if self.use_wsl:
                # Convert file paths in command to WSL paths
                # Note: cwd keeps Windows path because subprocess.run needs Windows path
                cmd = [self._to_wsl_path(arg) if os.path.exists(arg) or ('/' in arg and ':' not in arg) else arg 
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
        Convert Windows path to WSL path
        
        Example: C:/Users/name/file -> /mnt/c/Users/name/file
        """
        if not path or path.startswith('/'):
            return path
        
        # Handle Windows absolute path
        if len(path) >= 2 and path[1] == ':':
            drive = path[0].lower()
            rest = path[2:].replace('\\', '/')
            return f"/mnt/{drive}{rest}"
        
        # Relative path
        return path.replace('\\', '/')
    
    def compile(self, verilog_files: List[str], output_file: str, work_dir: str) -> Tuple[bool, str]:
        """
        Compile Verilog files
        
        Args:
            verilog_files: List of Verilog source files
            output_file: Output filename
            work_dir: Working directory
            
        Returns:
            (success, error_message)
        """
        cmd = ['iverilog', '-o', output_file] + verilog_files
        success, stdout, stderr = self._run_command(cmd, cwd=work_dir)
        
        if success:
            return True, ""
        else:
            return False, stderr or stdout
    
    def run_simulation(self, vvp_file: str, work_dir: str) -> Tuple[bool, str, str]:
        """
        Run simulation
        
        Args:
            vvp_file: vvp file path
            work_dir: Working directory
            
        Returns:
            (success, output_content, error_message)
        """
        cmd = ['vvp', vvp_file]
        success, stdout, stderr = self._run_command(cmd, cwd=work_dir)
        
        return success, stdout, stderr
    
    def execute(self, verilog_files: List[str], work_dir: str, vvp_name: str = "out.vvp") -> ExecutionResult:
        """
        Complete execution flow: compile + run
        
        Args:
            verilog_files: List of Verilog source files (testbench should be last)
            work_dir: Working directory
            vvp_name: Generated vvp filename
            
        Returns:
            ExecutionResult
        """
        vvp_path = os.path.join(work_dir, vvp_name)
        
        # Step 1: Compile
        compile_success, compile_error = self.compile(verilog_files, vvp_name, work_dir)
        
        if not compile_success:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Compilation failed:\n{compile_error}",
                compile_success=False,
                run_success=False
            )
        
        # Step 2: Run
        run_success, run_output, run_error = self.run_simulation(vvp_name, work_dir)
        
        # Find VCD file
        vcd_file = None
        if run_success:
            # Extract VCD filename from output
            vcd_match = re.search(r'\$dumpfile\("(.+?)"\)', ''.join(open(f).read() for f in verilog_files if os.path.exists(f)))
            if vcd_match:
                vcd_name = vcd_match.group(1)
                vcd_path = os.path.join(work_dir, vcd_name)
                if os.path.exists(vcd_path):
                    vcd_file = vcd_path
        
        # Combine error messages
        full_error = ""
        if run_error:
            full_error += run_error + "\n"
        if not run_success and not run_error:
            full_error = "Simulation execution failed"
        
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
        Extract values from $display output
        
        Expected format: "time=10 a=1 b=0 sel=0 out=1"
        
        Args:
            output: Simulation output
            
        Returns:
            List of values, each is a dict
        """
        values = []
        
        # Match key-value pair format
        pattern = r'time=(\d+)\s+(.+)'
        
        for line in output.split('\n'):
            line = line.strip()
            match = re.match(pattern, line)
            if match:
                time_val = int(match.group(1))
                rest = match.group(2)
                
                # Parse remaining key-value pairs
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
