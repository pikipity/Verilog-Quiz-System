"""
Verilog作业考试系统 - 主入口
"""
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
