"""
Flet主应用 - 页面路由和全局状态管理
"""
import flet as ft
from config import APP_NAME, WINDOW_WIDTH, WINDOW_HEIGHT
from ui.week_selector import WeekSelector
from ui.question_view import QuestionView


class VerilogQuizApp:
    """Verilog Quiz System Main Application"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self._setup_page()
        
        # Global state
        self.current_week = None
        self.current_question_index = 0
        self.drawn_questions = []
        
        # Initialize views
        self.week_selector = WeekSelector(self)
        self.question_view = QuestionView(self)
        
        # Show week selector
        self.show_week_selector()
    
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
    
    def show_snackbar(self, message: str, color=ft.Colors.BLUE):
        """Show snackbar"""
        snack = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=color,
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()
