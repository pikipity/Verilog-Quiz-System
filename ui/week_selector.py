"""
周次选择界面
"""
import os
import sys
import subprocess
import json
import threading
from datetime import datetime
import flet as ft
from config import QUESTIONS_DIR, SUBMISSIONS_DIR, SERVER_URL, BASE_DIR


class WeekSelector:
    """Week Selector Component"""
    
    def __init__(self, app):
        self.app = app
        self.weeks_data = []
        self.check_update_btn = None
    
    def build(self) -> ft.Control:
        """Build interface"""
        print(f"[DEBUG] WeekSelector.build() started")
        self._load_weeks_data()
        print(f"[DEBUG] Loaded {len(self.weeks_data)} weeks")
        
        try:
            header = self._build_header()
            print(f"[DEBUG] Header built OK")
            
            weeks_list = self._build_weeks_list()
            print(f"[DEBUG] Weeks list built OK")
            
            footer = self._build_footer()
            print(f"[DEBUG] Footer built OK")
            
            result = ft.Column(
                [
                    header,
                    ft.Divider(),
                    weeks_list,
                    ft.Divider(),
                    footer,
                ],
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            )
            print(f"[DEBUG] WeekSelector.build() completed successfully")
            return result
        except Exception as e:
            print(f"[ERROR] WeekSelector.build() failed: {e}")
            import traceback
            traceback.print_exc()
            # 返回一个错误提示界面，避免白屏
            return ft.Column([
                ft.Text(f"UI Error: {e}", color=ft.Colors.RED, size=16),
                ft.ElevatedButton("Reload", on_click=lambda e: self.app.show_week_selector()),
            ])
    
    def _build_header(self) -> ft.Control:
        """Build header"""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Verilog Quiz System",
                        size=32,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE,
                    ),
                    ft.Text(
                        "Select week to start assignment",
                        size=16,
                        color=ft.Colors.GREY,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=20,
            alignment=ft.Alignment.CENTER,
        )
    
    def _build_weeks_list(self) -> ft.Control:
        """Build weeks list"""
        print(f"[DEBUG] _build_weeks_list: weeks_data has {len(self.weeks_data)} items")
        
        if not self.weeks_data:
            print(f"[DEBUG] _build_weeks_list: returning empty state")
            return ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.FOLDER_OPEN, size=64, color=ft.Colors.GREY_400),
                        ft.Text("No questions available", size=18, color=ft.Colors.GREY),
                        ft.Text("Click button below to check for updates", size=14, color=ft.Colors.GREY_500),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                alignment=ft.Alignment.CENTER,
                expand=True,
            )
        
        week_cards = []
        for i, week_info in enumerate(self.weeks_data):
            print(f"[DEBUG] _build_weeks_list: building card {i+1}/{len(self.weeks_data)}")
            try:
                card = self._build_week_card(week_info)
                week_cards.append(card)
                week_cards.append(ft.Container(height=10))
                print(f"[DEBUG] _build_weeks_list: card {i+1} appended")
            except Exception as e:
                print(f"[ERROR] _build_weeks_list: card {i+1} failed: {e}")
                week_cards.append(ft.Text(f"Error loading week card: {e}", color=ft.Colors.RED))
        
        print(f"[DEBUG] _build_weeks_list: creating Column with {len(week_cards)} items")
        try:
            result = ft.Container(
                content=ft.Column(week_cards, scroll=ft.ScrollMode.AUTO),
                padding=ft.padding.symmetric(horizontal=20),
                expand=True,
            )
            print(f"[DEBUG] _build_weeks_list: Column created OK")
            return result
        except Exception as e:
            print(f"[ERROR] _build_weeks_list: Column creation failed: {e}")
            import traceback
            traceback.print_exc()
            return ft.Text(f"List Error: {e}", color=ft.Colors.RED)
    
    def _build_week_card(self, week_info: dict) -> ft.Control:
        """Build single week card (minimal version for ARM64 VM compatibility test)"""
        try:
            print(f"[DEBUG] _build_week_card: week_info={week_info}")
            
            week = week_info["week"]
            title = week_info.get("title", f"Week {week}")
            
            # Check progress for this week
            progress = self._get_week_progress(week)
            completed = progress["completed"]
            total = progress["total"]
            
            # Determine status text
            if completed >= total and total > 0:
                status_text = f"Completed {completed}/{total}"
                action_text = "Redo"
            elif completed > 0:
                status_text = f"In Progress {completed}/{total}"
                action_text = "Continue"
            else:
                status_text = f"Not Started 0/{total}"
                action_text = "Start"
            
            print(f"[DEBUG] _build_week_card: creating MINIMAL card for week={week}")
            
            # MINIMAL VERSION: Only use ft.Text and ft.Container
            # This avoids all potentially problematic widgets on ARM64:
            # - ft.Card (elevation/shadows)
            # - ft.ElevatedButton / ft.FilledButton (Material 3, complex rendering)
            # - ft.Icon (icon font loading)
            # - ft.Row with expand=True (layout calculation)
            # - ft.ButtonStyle
            card = ft.Container(
                content=ft.Text(
                    f"Week {week}: {title}  |  {status_text}  |  [{action_text}]",
                    size=16,
                ),
                padding=20,
                bgcolor=ft.Colors.WHITE,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=8,
                on_click=lambda e, w=week: self._on_week_click(w),
            )
            print(f"[DEBUG] _build_week_card: minimal card created OK")
            return card
        except Exception as e:
            print(f"[ERROR] _build_week_card failed for week_info={week_info}: {e}")
            import traceback
            traceback.print_exc()
            return ft.Container(
                content=ft.Text(f"Card Error: {e}", color=ft.Colors.RED),
                padding=20,
                border=ft.border.all(1, ft.Colors.RED),
            )
    
    def _build_footer(self) -> ft.Control:
        """Build footer"""
        self.check_update_btn = ft.ElevatedButton(
            "Check Update",
            icon=ft.Icons.REFRESH,
            on_click=self._on_check_update,
        )
        
        # 打开数据目录按钮
        open_data_btn = ft.TextButton(
            "Open Data Directory",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=self._on_open_data_directory,
            tooltip=f"Data location: {BASE_DIR}",
        )
        
        return ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            self.check_update_btn,
                            open_data_btn,
                        ],
                        spacing=10,
                    ),
                    ft.Text(
                        f"Server: {SERVER_URL}",
                        size=12,
                        color=ft.Colors.GREY,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=20,
        )
    
    def _load_weeks_data(self):
        """Load local weeks data"""
        self.weeks_data = []
        
        if not os.path.exists(QUESTIONS_DIR):
            return
        
        for item in os.listdir(QUESTIONS_DIR):
            week_dir = os.path.join(QUESTIONS_DIR, item)
            if not os.path.isdir(week_dir):
                continue
            
            if item.startswith("week"):
                info_file = os.path.join(week_dir, "info.json")
                if os.path.exists(info_file):
                    try:
                        with open(info_file, 'r', encoding='utf-8') as f:
                            info = json.load(f)
                            self.weeks_data.append(info)
                    except Exception as e:
                        print(f"Failed to read {info_file}: {e}")
        
        self.weeks_data.sort(key=lambda x: x.get("week", 0))
    
    def _get_week_progress(self, week: int) -> dict:
        """Get week progress (new format)"""
        draw_file = os.path.join(QUESTIONS_DIR, f"week{week}", "draw_result.json")
        total = 0
        if os.path.exists(draw_file):
            try:
                with open(draw_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    total = len(data.get("drawn_questions", []))
            except Exception:
                pass
        
        progress_file = os.path.join(SUBMISSIONS_DIR, f"week{week}", "progress.json")
        completed = 0
        if os.path.exists(progress_file):
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    questions = data.get("questions", {})
                    if isinstance(questions, dict):
                        completed = sum(1 for q in questions.values() if q.get("status") == "completed")
                    else:
                        completed = sum(1 for q in questions if q.get("status") == "completed")
            except Exception:
                pass
        
        return {"completed": completed, "total": total}
    
    def _on_week_click(self, week: int):
        """Week click event - auto jump to first incomplete question"""
        draw_file = os.path.join(QUESTIONS_DIR, f"week{week}", "draw_result.json")
        
        if not os.path.exists(draw_file):
            self.app.show_snackbar("Please click 'Check Update' to download questions first", ft.Colors.ORANGE)
            return
        
        # Read draw result
        try:
            with open(draw_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                drawn_questions = data.get("drawn_questions", [])
        except Exception:
            drawn_questions = []
        
        # Find index of first incomplete question
        start_index = 0
        for i, q_info in enumerate(drawn_questions):
            qid = q_info.get('id', '')
            if not self._is_question_completed(week, qid):
                start_index = i
                break
        
        self.app.show_question_view(week, start_index)
    
    def _is_question_completed(self, week: int, question_id: str) -> bool:
        """Check if specified question is completed"""
        if not question_id:
            return False
        
        progress_file = os.path.join(
            SUBMISSIONS_DIR, 
            f"week{week}", 
            question_id, 
            "progress.json"
        )
        
        if os.path.exists(progress_file):
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("status") == "completed"
            except Exception:
                pass
        
        return False
    
    def _on_open_data_directory(self, e):
        """Open data directory"""
        try:
            if sys.platform == 'win32':
                subprocess.run(['explorer', BASE_DIR])
            elif sys.platform == 'darwin':
                subprocess.run(['open', BASE_DIR])
            else:
                subprocess.run(['xdg-open', BASE_DIR])
            
            self.app.show_snackbar(f"Opened: {BASE_DIR}", ft.Colors.GREEN)
        except Exception as ex:
            self.app.show_snackbar(f"Cannot open directory: {ex}", ft.Colors.RED)
    
    def _on_check_update(self, e):
        """Check update button click"""
        from core.question_manager import question_manager
        import threading
        
        # Create full-screen loading overlay
        self.loading_overlay = ft.Container(
            content=ft.Column(
                [
                    ft.ProgressRing(width=50, height=50, stroke_width=4),
                    ft.Text("Connecting to server...", size=16, color=ft.Colors.WHITE),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            ),
            bgcolor=ft.Colors.BLACK54,
            alignment=ft.Alignment.CENTER,
            expand=True,
        )
        
        # Add to top of page
        self.app.page.overlay.append(self.loading_overlay)
        self.app.page.update()
        
        # Execute check in new thread
        def do_check():
            status, weeks, error_msg = question_manager.check_update()
            
            def update_ui():
                # Remove loading overlay
                if self.loading_overlay in self.app.page.overlay:
                    self.app.page.overlay.remove(self.loading_overlay)
                
                if status == "error":
                    def close_error(e):
                        error_dialog.open = False
                        self.app.page.update()
                    
                    error_dialog = ft.AlertDialog(
                        title=ft.Text("Connection Failed", color=ft.Colors.RED),
                        content=ft.Text(error_msg, selectable=True),
                        actions=[ft.ElevatedButton("OK", on_click=close_error)],
                        actions_alignment=ft.MainAxisAlignment.END,
                    )
                    self.app.page.overlay.append(error_dialog)
                    error_dialog.open = True
                
                elif status == "no_update":
                    self.app.show_snackbar("Already up to date", ft.Colors.GREEN)
                
                elif status == "success":
                    self._show_download_dialog(weeks)
                
                self.app.page.update()
            
            self.app.page.run_thread(update_ui)
        
        thread = threading.Thread(target=do_check)
        thread.daemon = True
        thread.start()
    
    def _show_download_dialog(self, weeks):
        """Show download dialog"""
        from core.question_manager import question_manager
        import threading
        
        def confirm_download(e):
            dialog.open = False
            self.app.page.update()
            
            # Create full-screen loading overlay
            self.loading_overlay = ft.Container(
                content=ft.Column(
                    [
                        ft.ProgressRing(width=50, height=50, stroke_width=4),
                        ft.Text(f"Downloading {len(weeks)} weeks...", size=16, color=ft.Colors.WHITE),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                ),
                bgcolor=ft.Colors.BLACK54,
                alignment=ft.Alignment.CENTER,
                expand=True,
            )
            
            # Add to top of page
            self.app.page.overlay.append(self.loading_overlay)
            self.app.page.update()
            
            # Execute download in new thread
            def do_download():
                success_count = 0
                for i, week in enumerate(weeks):
                    # Update prompt text
                    def update_text(idx=i):
                        if hasattr(self, 'loading_overlay') and self.loading_overlay:
                            self.loading_overlay.content.controls[1].value = f"Downloading Week {weeks[idx]}... ({idx+1}/{len(weeks)})"
                            self.app.page.update()
                    
                    self.app.page.run_thread(update_text)
                    
                    if question_manager.download_week(week):
                        success_count += 1
                
                def update_ui():
                    # Remove loading overlay
                    if hasattr(self, 'loading_overlay') and self.loading_overlay in self.app.page.overlay:
                        self.app.page.overlay.remove(self.loading_overlay)
                    
                    if success_count == len(weeks):
                        self.app.show_snackbar(f"Successfully downloaded {success_count} weeks", ft.Colors.GREEN)
                        self._load_weeks_data()
                        self.app.show_week_selector()
                    else:
                        self.app.show_snackbar(f"Download completed: {success_count}/{len(weeks)} weeks", ft.Colors.ORANGE)
                
                self.app.page.run_thread(update_ui)
            
            thread = threading.Thread(target=do_download)
            thread.daemon = True
            thread.start()
        
        def cancel(e):
            dialog.open = False
            self.app.page.update()
        
        weeks_str = ", ".join([f"Week {w}" for w in weeks])
        
        dialog = ft.AlertDialog(
            title=ft.Text("New Questions Available"),
            content=ft.Text(f"Found new questions:\n{weeks_str}\n\nDownload now?"),
            actions=[
                ft.TextButton("Cancel", on_click=cancel),
                ft.ElevatedButton("Download", on_click=confirm_download),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.app.page.overlay.append(dialog)
        dialog.open = True
        self.app.page.update()
