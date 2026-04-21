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
        self._load_weeks_data()
        
        return ft.Column(
            [
                self._build_header(),
                ft.Divider(),
                self._build_weeks_list(),
                ft.Divider(),
                self._build_footer(),
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )
    
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
        if not self.weeks_data:
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
        for week_info in self.weeks_data:
            card = self._build_week_card(week_info)
            week_cards.append(card)
            week_cards.append(ft.Container(height=10))
        
        return ft.Container(
            content=ft.Column(week_cards, scroll=ft.ScrollMode.AUTO),
            padding=ft.padding.symmetric(horizontal=20),
            expand=True,
        )
    
    def _build_week_card(self, week_info: dict) -> ft.Control:
        """Build single week card"""
        week = week_info["week"]
        title = week_info.get("title", f"Week {week}")
        
        # Check progress for this week
        progress = self._get_week_progress(week)
        completed = progress["completed"]
        total = progress["total"]
        
        # Determine status
        is_completed = completed >= total and total > 0
        is_in_progress = completed > 0 and not is_completed
        
        # Status colors and icons (not started status not shown)
        if is_completed:
            status_color = ft.Colors.GREEN
            status_icon = ft.Icons.CHECK_CIRCLE
            status_text = f"Completed {completed}/{total}"
            action_text = "Redo"
        elif is_in_progress:
            status_color = ft.Colors.ORANGE
            status_icon = ft.Icons.PENDING_ACTIONS
            status_text = f"In Progress {completed}/{total}"
            action_text = "Continue"
        else:
            status_color = ft.Colors.BLUE
            status_icon = ft.Icons.RADIO_BUTTON_OFF
            status_text = f"Not Started 0/{total}"  # Show not started status
            action_text = "Start"
        
        # Build left info column
        left_column_items = [
            ft.Text(
                f"Week {week}: {title}",
                size=20,
                weight=ft.FontWeight.BOLD,
            ),
        ]
        
        # Only show status row for non-not-started states
        if status_text:
            left_column_items.append(
                ft.Row(
                    [
                        ft.Icon(status_icon, color=status_color, size=20),
                        ft.Text(
                            status_text,
                            size=14,
                            color=status_color,
                            weight=ft.FontWeight.W_500,
                        ),
                    ],
                    spacing=5,
                ),
            )
        
        return ft.Card(
            content=ft.Container(
                content=ft.Row(
                    [
                        # Left: Week info
                        ft.Column(
                            left_column_items,
                            spacing=8,
                            expand=True,
                        ),
                        # Right: Action button
                        ft.ElevatedButton(
                            action_text,
                            icon=ft.Icons.PLAY_ARROW if action_text != "Redo" else ft.Icons.REFRESH,
                            on_click=lambda e, w=week: self._on_week_click(w),
                            style=ft.ButtonStyle(
                                color=ft.Colors.WHITE,
                                bgcolor=status_color,
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=20,
            ),
            elevation=2,
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
