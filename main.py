"""
Verilog作业考试系统 - 主入口
"""
import flet as ft
from ui.app import VerilogQuizApp


def main(page: ft.Page):
    """程序入口"""
    VerilogQuizApp(page)


def run_app():
    """启动应用"""
    ft.run(main)


if __name__ == "__main__":
    run_app()
