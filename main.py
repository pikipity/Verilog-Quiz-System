"""
Verilog作业考试系统 - 主入口
"""
import os
import sys


def _setup_linux_display_env():
    """
    Linux 显示环境优化（针对虚拟机、ARM64 和 GPU 受限环境）
    
    Flutter Linux embedder 在 VirtualBox 等 VM 的 GPU 虚拟化环境下
    可能因 OpenGL 驱动问题导致渲染崩溃（白屏）。
    此函数在导入 flet 之前检测环境并强制软件渲染。
    """
    if sys.platform != 'linux':
        return

    is_vm = False

    # 方法1: 通过 /proc/cpuinfo 检测 hypervisor 标志
    try:
        with open('/proc/cpuinfo', 'r', encoding='utf-8') as f:
            cpuinfo = f.read().lower()
            if any(x in cpuinfo for x in ['hypervisor', 'qemu', 'kvm', 'vmware']):
                is_vm = True
    except Exception:
        pass

    # 方法2: 通过 DMI product_name 检测
    try:
        with open('/sys/class/dmi/id/product_name', 'r', encoding='utf-8') as f:
            product = f.read().strip().lower()
            if any(x in product for x in ['virtualbox', 'vmware', 'kvm', 'qemu', 'bochs']):
                is_vm = True
    except Exception:
        pass

    # 方法3: 通过 systemd-detect-virt 检测
    if not is_vm:
        try:
            result = os.popen('systemd-detect-virt 2>/dev/null').read().strip().lower()
            if result and result != 'none':
                is_vm = True
        except Exception:
            pass

    # 方法4: 检查是否有可用的 GPU 渲染设备
    has_gpu = os.path.exists('/dev/dri')

    # 如果检测到 VM 或没有 GPU，强制软件渲染
    if is_vm or not has_gpu:
        os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'
        os.environ['GALLIUM_DRIVER'] = 'llvmpipe'
        print(f"[Display] VM/无GPU环境检测 (is_vm={is_vm}, has_gpu={has_gpu})，强制软件渲染")

    # VirtualBox + Wayland 组合已知有问题，强制使用 X11 后端
    if is_vm and 'GDK_BACKEND' not in os.environ:
        os.environ['GDK_BACKEND'] = 'x11'
        print(f"[Display] 强制 GDK_BACKEND=x11 以兼容 VM 环境")

    # 额外的 Mesa/Skia 安全设置
    if is_vm:
        os.environ['MESA_GLTHREAD'] = 'false'
        # 禁用 Zink（Vulkan->OpenGL 转译层），直接使用 llvmpipe
        os.environ['MESA_LOADER_DRIVER_OVERRIDE'] = 'llvmpipe'


# 必须在导入 flet 之前执行（flet 启动 Flutter embedder 子进程时会继承环境变量）
_setup_linux_display_env()

import flet as ft
from ui.app import VerilogQuizApp


def main(page: ft.Page):
    """Application entry"""
    VerilogQuizApp(page)


def run_app():
    """Launch application"""
    ft.run(main)


if __name__ == "__main__":
    run_app()
