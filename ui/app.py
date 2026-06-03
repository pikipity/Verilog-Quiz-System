"""
Flet主应用 - 页面路由和全局状态管理
"""
import flet as ft
import sys
from config import APP_NAME, WINDOW_WIDTH, WINDOW_HEIGHT
from ui.week_selector import WeekSelector
from ui.question_view import QuestionView
from core.code_executor import code_executor


class VerilogQuizApp:
    """Verilog Quiz System Main Application"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self._setup_page()
        
        # Check required dependencies before initializing views
        if code_executor.missing_tools:
            self._show_missing_tools_error(code_executor.missing_tools)
            return
        
        # Global state
        self.current_week = None
        self.current_question_index = 0
        self.drawn_questions = []
        
        # Initialize views
        self.week_selector = WeekSelector(self)
        self.question_view = QuestionView(self)
        
        # Show week selector
        self.show_week_selector()
    
    def _show_missing_tools_error(self, missing_tools: list):
        """Show error page when required tools are missing"""
        self.page.clean()
        
        tool_messages = {
            "iverilog": ("Icarus Verilog", "https://bleyer.co.uk/icarus/"),
            "GTKWave": ("GTKWave", "https://gtkwave.sourceforge.net/"),
        }
        
        tool_rows = []
        for tool in missing_tools:
            name, url = tool_messages.get(tool, (tool, ""))
            tool_rows.append(
                ft.Row([
                    ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED),
                    ft.Text(f"{name} ({tool})", size=16, weight=ft.FontWeight.BOLD),
                ], spacing=10)
            )
            if url:
                tool_rows.append(
                    ft.Text(f"  Download: {url}", size=12, color=ft.Colors.BLUE)
                )
        
        install_instructions = []
        if sys.platform == 'win32':
            install_instructions = [
                "Windows:",
                "  • iverilog: Download installer from the link above",
                "  • GTKWave: Download installer from the link above",
                "  • Or install both via WSL: sudo apt install iverilog gtkwave",
            ]
        elif sys.platform == 'darwin':
            install_instructions = [
                "macOS:",
                "  • brew install icarus-verilog",
                "  • brew install gtkwave",
            ]
        else:
            install_instructions = [
                "Linux (Ubuntu/Debian):",
                "  • sudo apt-get install iverilog gtkwave",
            ]
        
        error_content = ft.Column(
            [
                ft.Icon(ft.Icons.WARNING, size=64, color=ft.Colors.RED),
                ft.Text(
                    "Missing Required Dependencies",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.RED,
                ),
                ft.Text(
                    "The following tools are required but not detected on your system.",
                    size=14,
                    color=ft.Colors.GREY_700,
                ),
                ft.Divider(),
                *tool_rows,
                ft.Divider(),
                ft.Text(
                    "Installation Instructions:",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Column(
                    [ft.Text(line, size=13, color=ft.Colors.GREY_800) for line in install_instructions],
                    spacing=4,
                ),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Exit Application",
                    icon=ft.Icons.CLOSE,
                    on_click=lambda e: self.page.window.close(),
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.RED,
                    ),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
            expand=True,
        )
        
        self.page.add(
            ft.Container(
                content=error_content,
                padding=40,
                alignment=ft.Alignment.CENTER,
                expand=True,
            )
        )
        self.page.update()
    
    def _setup_page(self):
        """Configure page properties"""
        self.page.title = APP_NAME
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.window_width = WINDOW_WIDTH
        self.page.window_height = WINDOW_HEIGHT
        self.page.window_min_width = 1000
        self.page.window_min_height = 600
        
        # Set theme colors
        self.page.theme = ft.Theme(
            color_scheme_seed=ft.Colors.BLUE,
            visual_density=ft.VisualDensity.COMFORTABLE,
        )
        
        # Set window icon
        self.page.window.icon = "assets/icon.png"
        
        # Page scroll configuration
        self.page.scroll = ft.ScrollMode.AUTO
    
    def show_week_selector(self):
        """Show week selector"""
        self.page.clean()
        self.page.add(self.week_selector.build())
        self.page.update()
    
    def show_question_view(self, week: int, question_index: int = 0):
        """
        Show question view
        
        Args:
            week: Week number
            question_index: Question index (starting from 0)
        """
        self.current_week = week
        self.current_question_index = question_index
        
        self.page.clean()
        self.page.add(self.question_view.build(week, question_index))
        self.page.update()
    
    def navigate_to_question(self, question_index: int):
        """Navigate to specified question"""
        self.current_question_index = question_index
        self.show_question_view(self.current_week, question_index)
    
    def show_snackbar(self, message: str, color=ft.Colors.BLUE, duration=None):
        """Show snackbar"""
        snack = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=color,
        )
        if duration is not None:
            snack.duration = duration
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()
