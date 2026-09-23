"""
GTKWave 辅助模块 - 跨平台启动 GTKWave 并自动生成 Tcl 脚本
"""
import os
import re
import subprocess
import sys


def extract_signals_from_vcd(vcd_file: str) -> list:
    """Extract all signal names from VCD file.

    Icarus Verilog's $dumpvars dumps signals in both the testbench top-level
    and the DUT sub-module, often with DIFFERENT identifiers for the same
    port-connected signal. We deduplicate by base signal name (e.g. 'a'),
    keeping the deepest hierarchical path (the DUT port view).
    """
    try:
        with open(vcd_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        scope_stack = []
        all_signals = []  # list of (full_path, base_name, depth)
        in_var = False
        var_parts = []

        for raw_line in content.split('\n'):
            line = raw_line.strip()

            if line.startswith('$scope'):
                parts = line.split()
                if len(parts) >= 3:
                    scope_stack.append(parts[2])
                in_var = False
            elif line.startswith('$upscope'):
                if scope_stack:
                    scope_stack.pop()
                in_var = False
            elif line.startswith('$var'):
                var_parts = line.split()
                if '$end' in line:
                    if len(var_parts) >= 5:
                        name = var_parts[4]
                        if scope_stack:
                            full_name = '.'.join(scope_stack) + '.' + name
                        else:
                            full_name = name
                        depth = full_name.count('.')
                        all_signals.append((full_name, name, depth))
                    in_var = False
                else:
                    in_var = True
            elif in_var and line.startswith('$end'):
                if len(var_parts) >= 5:
                    name = var_parts[4]
                    if scope_stack:
                        full_name = '.'.join(scope_stack) + '.' + name
                    else:
                        full_name = name
                    depth = full_name.count('.')
                    all_signals.append((full_name, name, depth))
                in_var = False
                var_parts = []
            elif in_var:
                var_parts.extend(line.split())

        if not all_signals:
            return []

        # Deduplicate by base signal name, keep DEEPEST path
        name_to_best = {}
        for full_name, base_name, depth in all_signals:
            if base_name not in name_to_best:
                name_to_best[base_name] = (full_name, depth)
            elif depth > name_to_best[base_name][1]:
                name_to_best[base_name] = (full_name, depth)

        result = [info[0] for info in name_to_best.values()]
        result.sort(key=lambda s: (s.count('.'), s))
        return result
    except Exception as e:
        print(f"Error extracting signals from VCD: {e}")
        return []


def create_gtkwave_tcl_script(vcd_file: str, script_path: str) -> bool:
    """Create a Tcl script to add all signals and zoom to fit"""
    signals = extract_signals_from_vcd(vcd_file)
    if not signals:
        return False

    try:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write("# GTKWave Tcl script - auto-generated\n")
            f.write("# Add all signals\n")

            for sig in signals:
                escaped_sig = sig.replace('[', '\\[').replace(']', '\\]')
                f.write(f'gtkwave::addSignalsFromList "{escaped_sig}"\n')

            f.write("\n# Zoom to fit\n")
            f.write("gtkwave::/Time/Zoom/Zoom_Full\n")

        return True
    except Exception as e:
        print(f"Error creating Tcl script: {e}")
        return False


def _check_gtkwave_in_wsl() -> bool:
    """Check if GTKWave is installed in WSL"""
    try:
        result = subprocess.run(
            ['wsl', 'which', 'gtkwave'],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception as e:
        print(f"WSL check error: {e}")
        return False


def _launch_gtkwave_windows_native(gtkwave_path: str, vcd: str, script: str = None):
    """Launch native Windows GTKWave"""
    if script and os.path.exists(script):
        return subprocess.Popen([gtkwave_path, '-S', script, vcd],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
    else:
        return subprocess.Popen([gtkwave_path, vcd],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)


def _launch_gtkwave_wsl(vcd: str, script: str = None):
    """Launch WSL GTKWave with Windows path conversion"""
    drive = vcd[0].lower()
    path_part = vcd[2:].replace('\\', '/')
    wsl_vcd = f"/mnt/{drive}{path_part}"

    wsl_script = None
    if script and os.path.exists(script):
        script_drive = script[0].lower()
        script_path_part = script[2:].replace('\\', '/')
        wsl_script = f"/mnt/{script_drive}{script_path_part}"

    if wsl_script:
        return subprocess.Popen(
            ['wsl', 'DISPLAY=:0', 'gtkwave', '-S', wsl_script, wsl_vcd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        return subprocess.Popen(
            ['wsl', 'DISPLAY=:0', 'gtkwave', wsl_vcd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )


def open_vcd_in_gtkwave(vcd_file: str, label: str) -> tuple:
    """Open specific VCD file in GTKWave with all signals displayed (Cross-platform).

    Returns:
        (success: bool, message: str)
    """
    print(f"[GTKWave] Opening {label} VCD: {vcd_file}")

    if not vcd_file:
        return False, f"{label} VCD file path is empty"

    if not os.path.exists(vcd_file):
        return False, f"{label} VCD file not found: {os.path.basename(vcd_file)}"

    try:
        temp_dir = os.path.dirname(vcd_file)
        safe_label = label.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')
        tcl_script = os.path.join(temp_dir, f"gtkwave_{safe_label}_signals.tcl")
        has_script = create_gtkwave_tcl_script(vcd_file, tcl_script)

        platform = sys.platform

        if platform == 'win32':
            gtkwave_found = False
            error_msg = ""

            gtkwave_paths = [
                r"C:\Program Files\GTKWave\bin\gtkwave.exe",
                r"C:\Program Files (x86)\GTKWave\bin\gtkwave.exe",
            ]
            for path in gtkwave_paths:
                if os.path.exists(path):
                    try:
                        _launch_gtkwave_windows_native(
                            path, vcd_file,
                            tcl_script if has_script else None
                        )
                        gtkwave_found = True
                        print(f"Opened native GTKWave: {path}")
                        break
                    except Exception as e:
                        error_msg = f"Native GTKWave error: {e}"
                        print(error_msg)

            if not gtkwave_found and _check_gtkwave_in_wsl():
                try:
                    _launch_gtkwave_wsl(
                        vcd_file,
                        tcl_script if has_script else None
                    )
                    gtkwave_found = True
                    print("Launched WSL GTKWave")
                except Exception as e:
                    error_msg = f"WSL GTKWave error: {e}"
                    print(error_msg)

            if gtkwave_found:
                return True, f"Opening {label} in GTKWave..."
            else:
                full_msg = "GTKWave not found or failed to open.\n\n"
                full_msg += "Installation options:\n"
                full_msg += "1. Windows: Install from http://gtkwave.sourceforge.net/\n"
                full_msg += "2. WSL: sudo apt install gtkwave\n\n"
                full_msg += f"Error: {error_msg[:100]}"
                return False, full_msg

        elif platform == 'darwin':
            try:
                cmd = ['open', '-a', 'GTKWave', vcd_file]
                if has_script and os.path.exists(tcl_script):
                    try:
                        subprocess.Popen(
                            ['gtkwave', '-S', tcl_script, vcd_file],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        print("Launched macOS GTKWave with script")
                    except Exception:
                        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        print("Launched macOS GTKWave via open -a")
                else:
                    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print("Launched macOS GTKWave via open -a")

                return True, f"Opening {label} in GTKWave..."
            except Exception as e:
                try:
                    if has_script and os.path.exists(tcl_script):
                        subprocess.Popen(
                            ['gtkwave', '-S', tcl_script, vcd_file],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                    else:
                        subprocess.Popen(
                            ['gtkwave', vcd_file],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                    return True, f"Opening {label} in GTKWave..."
                except Exception as e2:
                    return False, "GTKWave not found. Install with: brew install gtkwave"

        else:
            try:
                if has_script and os.path.exists(tcl_script):
                    subprocess.Popen(
                        ['gtkwave', '-S', tcl_script, vcd_file],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    print(f"Launched Linux GTKWave with script: {tcl_script}")
                else:
                    subprocess.Popen(
                        ['gtkwave', vcd_file],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    print("Launched Linux GTKWave without script")

                return True, f"Opening {label} in GTKWave..."
            except Exception as e:
                return False, "GTKWave not found. Install with: sudo apt install gtkwave"

    except Exception as ex:
        return False, f"Failed to open GTKWave: {ex}"
