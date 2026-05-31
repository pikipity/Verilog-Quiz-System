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
        print(f"[DEBUG] show_week_selector called")
        try:
            # 使用 controls.clear() 替代 page.clean()，避免触发 FlutterEngineRemoveView
            # 在 VirtualBox 等 VM 环境中，page.clean() 可能导致 implicit view 移除错误
            self.page.controls.clear()
            print(f"[DEBUG] controls cleared, building week_selector...")
            content = self.week_selector.build()
            print(f"[DEBUG] week_selector.build() returned, type={type(content)}")
            self.page.add(content)
            print(f"[DEBUG] content added to page")
            self.page.update()
            print(f"[DEBUG] page.update() called")
        except Exception as e:
            print(f"[ERROR] show_week_selector failed: {e}")
            import traceback
            traceback.print_exc()
            # 降级处理：直接替换 controls 列表
            try:
                self.page.controls = [self.week_selector.build()]
                self.page.update()
            except Exception as e2:
                print(f"[ERROR] Fallback also failed: {e2}")
                traceback.print_exc()
    
    def show_question_view(self, week: int, question_index: int = 0):
        """
        Show question view
        
        Args:
            week: Week number
            question_index: Question index (starting from 0)
        """
        self.current_week = week
        self.current_question_index = question_index
        
        print(f"[DEBUG] show_question_view called: week={week}, index={question_index}")
        try:
            self.page.controls.clear()
            content = self.question_view.build(week, question_index)
            self.page.add(content)
            self.page.update()
            print(f"[DEBUG] show_question_view completed")
        except Exception as e:
            print(f"[ERROR] show_question_view failed: {e}")
            import traceback
            traceback.print_exc()
            try:
                self.page.controls = [self.question_view.build(week, question_index)]
                self.page.update()
            except Exception as e2:
                print(f"[ERROR] Fallback also failed: {e2}")
                traceback.print_exc()
    
    def navigate_to_question(self, question_index: int):
        """Navigate to specified question"""
        self.current_question_index = question_index
        self.show_question_view(self.current_week, question_index)
    
    def show_snackbar(self, message: str, color=ft.Colors.BLUE, duration=None):
        """Show snackbar"""
        try:
            snack = ft.SnackBar(
                content=ft.Text(message),
                bgcolor=color,
                duration=duration,
            )
            self.page.overlay.append(snack)
            snack.open = True
            self.page.update()
        except Exception as e:
            print(f"[Error] show_snackbar failed: {e}")
