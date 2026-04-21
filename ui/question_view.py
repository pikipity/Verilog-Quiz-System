"""
答题界面
"""
import os
import json
import re
from datetime import datetime
import flet as ft
from config import (
    QUESTIONS_DIR, 
    SUBMISSIONS_DIR, 
    CODE_FONT, 
    CODE_FONT_SIZE,
    AUTO_SAVE_INTERVAL
)
from core.code_executor import code_executor, ExecutionResult
from core.result_analyzer import result_analyzer, AnalysisResult
from core.question_manager import question_manager
from core.crypto_manager import crypto_manager


class QuestionView:
    """Question View Component"""
    
    def __init__(self, app):
        self.app = app
        self.code_editor = None
        self.save_timer = None
        self.current_code = ""
        self.week = None
        self.question_index = None
        self.question_id = None  # 题目唯一ID
        self.question_info = None  # 题目完整信息（含folder, title）
    
    def build(self, week: int, question_index: int) -> ft.Control:
        """Build question view"""
        self.week = week
        self.question_index = question_index
        
        # 加载题目信息
        self._load_question_info()
        
        if not self.question_id:
            return ft.Column([
                ft.Text("Failed to load question", size=24, color=ft.Colors.RED),
                ft.ElevatedButton("Back", on_click=lambda e: self.app.show_week_selector())
            ])
        
        # 加载已有代码（使用ID命名）
        existing_code = self._load_existing_code()
        
        # 加载testbench代码
        testbench_code = self._load_testbench_code()
        
        # 单列垂直布局，整个页面可滚动
        return ft.Column(
            [
                self._build_header(),
                ft.Divider(height=1),
                # 题目选择块
                self._build_question_selector(),
                ft.Divider(height=1),
                # 题目描述
                self._build_question_panel(),
                ft.Divider(height=1),
                # Code editor
                self._build_editor_panel(existing_code),
                ft.Divider(height=1),
                # 测试平台
                self._build_testbench_panel(testbench_code),
                ft.Divider(height=1),
                # 底部按钮
                self._build_footer(),
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )
    
    def _build_header(self) -> ft.Control:
        """构建顶部导航栏"""
        total = len(self.app.drawn_questions) if self.app.drawn_questions else 0
        current = self.question_index + 1
        
        # 获取题目标题
        title = self.question_info.get('title', f'题目{current}') if self.question_info else f'题目{current}'
        
        return ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        tooltip="Back to week list",
                        on_click=lambda e: self.app.show_week_selector(),
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                f"Week {self.week} - 题目 {current}/{total}",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                title,
                                size=14,
                                color=ft.Colors.GREY,
                            ),
                        ],
                        spacing=2,
                    ),
                    ft.Container(
                        content=ft.Text(
                            f"ID: {self.question_id}",
                            size=11,
                            color=ft.Colors.GREY,
                        ),
                        padding=ft.padding.only(right=10),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
        )
    
    def _build_question_selector(self) -> ft.Control:
        """Build question selector (quick jump)"""
        total = len(self.app.drawn_questions) if self.app.drawn_questions else 0
        
        if total == 0:
            return ft.Container()
        
        # 构建题目按钮列表
        question_buttons = []
        for i in range(total):
            q_info = self.app.drawn_questions[i] if i < len(self.app.drawn_questions) else {}
            q_title = q_info.get('title', f'题{i+1}')
            is_current = i == self.question_index
            
            # 检查题目完成状态
            is_completed = self._is_question_completed(i, q_info.get('id', ''))
            
            # 根据状态设置颜色
            if is_current:
                bg_color = ft.Colors.BLUE
                text_color = ft.Colors.WHITE
                icon = ft.Icons.EDIT
            elif is_completed:
                bg_color = ft.Colors.GREEN_100
                text_color = ft.Colors.GREEN
                icon = ft.Icons.CHECK_CIRCLE
            else:
                bg_color = ft.Colors.GREY_100
                text_color = ft.Colors.GREY_700
                icon = ft.Icons.RADIO_BUTTON_UNCHECKED
            
            btn = ft.ElevatedButton(
                content=ft.Row(
                    [
                        ft.Icon(icon, size=16, color=text_color),
                        ft.Text(
                            f"{i+1}. {q_title}",
                            size=12,
                            color=text_color,
                            weight=ft.FontWeight.BOLD if is_current else ft.FontWeight.NORMAL,
                        ),
                    ],
                    spacing=4,
                ),
                style=ft.ButtonStyle(
                    bgcolor=bg_color,
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                ),
                on_click=lambda e, idx=i: self._on_question_select(idx),
                disabled=is_current,  # 当前题目禁用点击
            )
            question_buttons.append(btn)
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Question Selection", size=14, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=1),
                    ft.Row(
                        question_buttons,
                        spacing=8,
                        wrap=True,  # 允许换行
                    ),
                ],
                spacing=5,
            ),
            padding=10,
            border=ft.border.all(1, ft.Colors.BLUE_200),
            border_radius=8,
            bgcolor=ft.Colors.BLUE_50,
        )
    
    def _is_question_completed(self, index: int, question_id: str) -> bool:
        """Check if specified question is completed"""
        if not question_id:
            return False
        
        progress_file = os.path.join(
            SUBMISSIONS_DIR, 
            f"week{self.week}", 
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
    
    def _on_question_select(self, index: int):
        """Question selection button click"""
        if index != self.question_index:
            # 先保存当前代码
            self._save_code()
            # 跳转到选择的题目
            self.app.navigate_to_question(index)
    
    def _build_question_panel(self) -> ft.Control:
        """Build question display panel"""
        question_md = self._load_question_markdown()
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Question Description", size=16, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=1),
                    ft.Markdown(
                        question_md,
                        selectable=True,
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                        code_theme=ft.MarkdownCodeTheme.GITHUB,
                    ),
                ],
                spacing=5,
            ),
            padding=10,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
        )
    
    def _build_editor_panel(self, existing_code: str) -> ft.Control:
        """Build code editor panel (with line numbers)"""
        self.current_code = existing_code
        
        # Auto-save function (when focus is lost)
        def on_blur_save(e):
            """Auto-save when focus is lost"""
            if self._save_code():
                print(f"Auto-saved: {self.question_id}.v")
        
        # Calculate line numbers
        line_count = existing_code.count('\n') + 1 if existing_code else 1
        line_numbers_text = '\n'.join(str(i) for i in range(1, line_count + 1))
        
        # Line number display component (read-only)
        self.editor_line_numbers = ft.TextField(
            value=line_numbers_text,
            multiline=True,
            min_lines=15,
            max_lines=None,
            text_style=ft.TextStyle(
                font_family=CODE_FONT,
                size=CODE_FONT_SIZE,
                color=ft.Colors.GREY_500,
            ),
            border_color=ft.Colors.TRANSPARENT,
            read_only=True,
            bgcolor=ft.Colors.GREY_100,
            width=50,
            content_padding=ft.padding.only(left=8, right=4, top=12, bottom=12),
        )
        
        # 代码编辑器
        self.code_editor = ft.TextField(
            value=existing_code,
            multiline=True,
            min_lines=15,
            max_lines=None,
            text_style=ft.TextStyle(
                font_family=CODE_FONT,
                size=CODE_FONT_SIZE,
            ),
            border_color=ft.Colors.BLUE_400,
            hint_text="Write your Verilog code here...",
            on_change=self._on_code_change_with_line_numbers,
            on_blur=on_blur_save,  # Auto-save when focus is lost
            expand=True,
            content_padding=ft.padding.only(left=8, top=12, bottom=12),
        )
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Code Editor", size=16, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=1),
                    ft.Row(
                        [
                            self.editor_line_numbers,
                            ft.VerticalDivider(width=1, color=ft.Colors.GREY_300),
                            self.code_editor,
                        ],
                        spacing=0,
                        expand=True,
                    ),
                ],
                spacing=5,
            ),
            padding=10,
            border=ft.border.all(1, ft.Colors.BLUE_200),
            border_radius=8,
        )
    
    def _build_testbench_panel(self, testbench_code: str) -> ft.Control:
        """Build testbench panel (read-only, with line numbers)"""
        # 计算行号
        line_count = testbench_code.count('\n') + 1 if testbench_code else 1
        line_numbers_text = '\n'.join(str(i) for i in range(1, line_count + 1))
        
        # Line numbers display
        tb_line_numbers = ft.TextField(
            value=line_numbers_text,
            multiline=True,
            min_lines=10,
            max_lines=None,
            text_style=ft.TextStyle(
                font_family=CODE_FONT,
                size=CODE_FONT_SIZE,
                color=ft.Colors.GREY_500,
            ),
            border_color=ft.Colors.TRANSPARENT,
            read_only=True,
            bgcolor=ft.Colors.GREY_100,
            width=50,
            content_padding=ft.padding.only(left=8, right=4, top=12, bottom=12),
        )
        
        # Testbench code display
        tb_code = ft.TextField(
            value=testbench_code,
            multiline=True,
            min_lines=10,
            max_lines=None,
            text_style=ft.TextStyle(
                font_family=CODE_FONT,
                size=CODE_FONT_SIZE,
            ),
            border_color=ft.Colors.GREY_400,
            read_only=True,
            bgcolor=ft.Colors.GREY_50,
            expand=True,
            content_padding=ft.padding.only(left=8, top=12, bottom=12),
        )
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Testbench", size=16, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=1),
                    ft.Row(
                        [
                            tb_line_numbers,
                            ft.VerticalDivider(width=1, color=ft.Colors.GREY_300),
                            tb_code,
                        ],
                        spacing=0,
                        expand=True,
                    ),
                ],
                spacing=5,
            ),
            padding=10,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
        )
    
    def _load_testbench_code(self) -> str:
        """Load testbench code"""
        if not self.question_id:
            return "// Cannot load testbench"
        
        tb_path = os.path.join(
            QUESTIONS_DIR, 
            f"week{self.week}", 
            self.question_id,
            "testbench.v"
        )
        
        if os.path.exists(tb_path):
            try:
                with open(tb_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Normalize line endings to \n to avoid extra blank lines from Windows \r\n
                    return content.replace('\r\n', '\n')
            except Exception as e:
                return f"// Failed to read testbench: {e}"
        
        return "// Testbench file does not exist"
    
    def _build_footer(self) -> ft.Control:
        """Build footer action bar"""
        self.status_text = ft.Text(
            "Ready",
            size=12,
            color=ft.Colors.GREY,
        )
        
        # Check if this is the first question
        is_first = self.question_index == 0
        
        return ft.Container(
            content=ft.Row(
                [
                    self.status_text,
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Previous",
                                icon=ft.Icons.ARROW_BACK,
                                on_click=self._on_prev_question,
                                disabled=is_first,
                            ),
                            ft.ElevatedButton(
                                "Run Test",
                                icon=ft.Icons.PLAY_ARROW,
                                on_click=self._on_run_test,
                                style=ft.ButtonStyle(
                                    color=ft.Colors.WHITE,
                                    bgcolor=ft.Colors.GREEN,
                                ),
                            ),
                            ft.ElevatedButton(
                                "Save & Continue",
                                icon=ft.Icons.SAVE,
                                on_click=self._on_save_and_continue,
                            ),
                        ],
                        spacing=10,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=10,
        )
    
    def _load_question_info(self):
        """Load question info (including ID, folder, title)"""
        # Read draw result
        draw_file = os.path.join(QUESTIONS_DIR, f"week{self.week}", "draw_result.json")
        
        if os.path.exists(draw_file):
            try:
                with open(draw_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.app.drawn_questions = data.get("drawn_questions", [])
                    
                    if self.question_index < len(self.app.drawn_questions):
                        self.question_info = self.app.drawn_questions[self.question_index]
                        self.question_id = self.question_info['id']
            except Exception as e:
                print(f"Failed to read draw result: {e}")
    
    def _load_question_markdown(self) -> str:
        """Load question Markdown content (using ID as directory name)"""
        import base64
        
        if not self.question_id:
            return "# Failed to load question\n\nPlease return and reselect the week."
        
        # Use ID as subdirectory name
        md_file = os.path.join(
            QUESTIONS_DIR, 
            f"week{self.week}", 
            self.question_id,
            "question.md"
        )
        
        if os.path.exists(md_file):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Convert local images to base64 for embedded display
                question_dir = os.path.dirname(md_file)
                
                def replace_image_with_base64(match):
                    alt_text = match.group(1)
                    img_path = match.group(2)
                    
                    # Skip if already a URL or data URI
                    if img_path.startswith(('http://', 'https://', 'data:')):
                        return match.group(0)
                    
                    # Get absolute path to image
                    abs_img_path = os.path.join(question_dir, img_path)
                    
                    if os.path.exists(abs_img_path):
                        try:
                            # Read image and convert to base64
                            with open(abs_img_path, 'rb') as img_file:
                                img_data = img_file.read()
                                base64_data = base64.b64encode(img_data).decode('utf-8')
                            
                            # Determine MIME type from extension
                            ext = os.path.splitext(img_path)[1].lower()
                            mime_types = {
                                '.png': 'image/png',
                                '.jpg': 'image/jpeg',
                                '.jpeg': 'image/jpeg',
                                '.gif': 'image/gif',
                                '.svg': 'image/svg+xml',
                                '.bmp': 'image/bmp',
                                '.webp': 'image/webp'
                            }
                            mime_type = mime_types.get(ext, 'image/png')
                            
                            return f'![{alt_text}](data:{mime_type};base64,{base64_data})'
                        except Exception as e:
                            print(f"Failed to embed image {img_path}: {e}")
                            return f'![{alt_text}]({img_path})'
                    else:
                        print(f"Image not found: {abs_img_path}")
                        return f'![{alt_text}]({img_path})'
                
                content = re.sub(
                    r'!\[([^\]]*)\]\(([^)]+)\)',
                    replace_image_with_base64,
                    content
                )
                return content
            except Exception as e:
                return f"# Failed to read question\n\n{e}"
        
        return "# Question file does not exist\n\nPlease check for updates."
    
    def _load_existing_code(self) -> str:
        """Load existing code (using ID naming, organized by question subfolder)"""
        if not self.question_id:
            return self._get_code_template()
        
        # Use ID as subdirectory and filename
        code_file = os.path.join(
            SUBMISSIONS_DIR,
            f"week{self.week}",
            self.question_id,
            f"{self.question_id}.v"
        )
        
        if os.path.exists(code_file):
            try:
                with open(code_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Normalize line endings to \n to avoid extra blank lines from Windows \r\n
                    return content.replace('\r\n', '\n')
            except Exception as e:
                print(f"Failed to read existing code: {e}")
        
        return self._get_code_template()
    
    def _get_code_template(self) -> str:
        """Get code template"""
        return """// Write your Verilog code here

module my_module (
    // Define ports
);
    
    // Implement logic
    
endmodule
"""
    
    def _on_code_change(self, e):
        """Code change event"""
        self._update_code_status(e.control.value)
    
    def _on_code_change_with_line_numbers(self, e):
        """Code change event (sync update line numbers)"""
        value = e.control.value
        self._update_code_status(value)
        self._update_editor_line_numbers(value)
    
    def _update_editor_line_numbers(self, code: str):
        """Update code editor line numbers"""
        if hasattr(self, 'editor_line_numbers'):
            line_count = code.count('\n') + 1 if code else 1
            line_numbers_text = '\n'.join(str(i) for i in range(1, line_count + 1))
            self.editor_line_numbers.value = line_numbers_text
            self.editor_line_numbers.update()
    
    def _update_code_status(self, value: str):
        """Update code status"""
        self.current_code = value
        self.status_text.value = "Unsaved changes"
        self.status_text.color = ft.Colors.ORANGE
        self.status_text.update()
    
    def _save_code(self) -> bool:
        """Save code (using ID naming, organized by question subfolder)"""
        if not self.question_id:
            return False
        
        # Ensure directory exists: submissions/weekX/question_id/
        question_dir = os.path.join(SUBMISSIONS_DIR, f"week{self.week}", self.question_id)
        os.makedirs(question_dir, exist_ok=True)
        
        # Save code file
        code_file = os.path.join(question_dir, f"{self.question_id}.v")
        
        try:
            # Use \n as line ending when saving
            normalized_code = self.current_code.replace('\r\n', '\n').replace('\r', '\n')
            with open(code_file, 'w', encoding='utf-8', newline='\n') as f:
                f.write(normalized_code)
            
            # Update progress
            self._update_progress()
            
            self.status_text.value = f"Saved {datetime.now().strftime('%H:%M:%S')}"
            self.status_text.color = ft.Colors.GREEN
            self.status_text.update()
            
            return True
        except Exception as e:
            self.status_text.value = f"Save failed: {e}"
            self.status_text.color = ft.Colors.RED
            self.status_text.update()
            return False
    
    def _update_progress(self, status: str = "in_progress"):
        """Update progress file (record with ID, saved in question subfolder)"""
        question_dir = os.path.join(SUBMISSIONS_DIR, f"week{self.week}", self.question_id)
        os.makedirs(question_dir, exist_ok=True)
        
        progress_file = os.path.join(question_dir, "progress.json")
        
        progress_data = {}
        
        # Read existing progress
        if os.path.exists(progress_file):
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
            except Exception:
                pass
        
        # Update current question status
        progress_data.update({
            "question_id": self.question_id,
            "index": self.question_index,
            "title": self.question_info.get('title', '') if self.question_info else '',
            "status": status,
            "last_save": datetime.now().isoformat(),
        })
        
        try:
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to update progress: {e}")
        
        # Also update weekly progress file
        self._update_week_progress(status)
    
    def _update_week_progress(self, status: str = "in_progress"):
        """Update weekly progress file (for week_selector to read)"""
        week_dir = os.path.join(SUBMISSIONS_DIR, f"week{self.week}")
        os.makedirs(week_dir, exist_ok=True)
        
        week_progress_file = os.path.join(week_dir, "progress.json")
        
        week_data = {"questions": {}}
        
        # Read existing weekly progress
        if os.path.exists(week_progress_file):
            try:
                with open(week_progress_file, 'r', encoding='utf-8') as f:
                    week_data = json.load(f)
                    if "questions" not in week_data:
                        week_data["questions"] = {}
            except Exception:
                pass
        
        # 更新当前题目状态
        week_data["questions"][self.question_id] = {
            "status": status,
            "index": self.question_index,
            "title": self.question_info.get('title', '') if self.question_info else '',
            "last_update": datetime.now().isoformat(),
        }
        
        try:
            with open(week_progress_file, 'w', encoding='utf-8') as f:
                json.dump(week_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to update weekly progress: {e}")
    
    def _on_run_test(self, e):
        """Run test button click"""
        if not self._save_code():
            self.app.show_snackbar("Failed to save code, cannot test", ft.Colors.RED)
            return
        
        # Run test
        self._run_test_workflow()
    
    def _run_test_workflow(self):
        """Run complete test workflow (temp files in submissions question directory)"""
        import threading
        
        # Show loading overlay
        loading_text = ft.Text("Preparing test environment...", size=16, color=ft.Colors.WHITE)
        loading_overlay = ft.Container(
            content=ft.Column(
                [
                    ft.ProgressRing(width=50, height=50, stroke_width=4),
                    loading_text,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            ),
            bgcolor=ft.Colors.BLACK54,
            alignment=ft.Alignment.CENTER,
            expand=True,
        )
        self.app.page.overlay.append(loading_overlay)
        self.app.page.update()
        
        def update_message(msg: str):
            """Update progress message (thread-safe)"""
            def _update():
                loading_text.value = msg
                self.app.page.update()
            self.app.page.run_thread(_update)
        
        def show_snackbar_safe(text, color):
            """Safely show snackbar"""
            def _show():
                self.app.show_snackbar(text, color)
            self.app.page.run_thread(_show)
        
        def close_overlay():
            """Close overlay"""
            def _close():
                try:
                    if loading_overlay in self.app.page.overlay:
                        self.app.page.overlay.remove(loading_overlay)
                        self.app.page.update()
                except Exception:
                    pass
            self.app.page.run_thread(_close)
        
        def run_test_thread():
            """Run test in background thread"""
            try:
                # 1. Get reference code
                update_message("Getting reference answer...")
                ref_code = question_manager.get_reference_code(self.week, self.question_id)
                
                # 2. Create temp working directory
                update_message("Preparing simulation environment...")
                question_dir = os.path.join(SUBMISSIONS_DIR, f"week{self.week}", self.question_id)
                temp_dir = os.path.join(question_dir, "temp")
                os.makedirs(temp_dir, exist_ok=True)
                
                if ref_code is None:
                    show_snackbar_safe("Cannot get reference answer", ft.Colors.RED)
                    close_overlay()
                    return
                
                # 3. Read testbench
                update_message("Reading testbench...")
                tb_path = os.path.join(QUESTIONS_DIR, f"week{self.week}", self.question_id, "testbench.v")
                
                if not os.path.exists(tb_path):
                    show_snackbar_safe("Testbench file not found", ft.Colors.RED)
                    close_overlay()
                    return
                
                with open(tb_path, 'r', encoding='utf-8') as f:
                    testbench = f.read()
                
                # 4. Write student code
                student_file = os.path.join(temp_dir, "student.v")
                with open(student_file, 'w', encoding='utf-8') as f:
                    f.write(self.current_code)
                
                # 5. Write reference code
                ref_file = os.path.join(temp_dir, "reference.v")
                with open(ref_file, 'w', encoding='utf-8') as f:
                    f.write(ref_code)
                
                # 6. Execute reference code test
                update_message("Running reference simulation...")
                ref_result = code_executor.execute([ref_file, tb_path], temp_dir, "ref.vvp")
                
                # 7. Execute student code test
                update_message("Running student code simulation...")
                student_result = code_executor.execute([student_file, tb_path], temp_dir, "student.vvp")
                
                # 8. Save results
                update_message("Saving test results...")
                self._save_test_result(student_result)
                
                # 9. Display results and update UI (in main thread)
                def update_ui():
                    self._show_test_result_dialog(student_result, ref_result, testbench)
                    
                    if student_result.compile_success:
                        if student_result.run_success:
                            self.status_text.value = "Test completed"
                            self.status_text.color = ft.Colors.GREEN
                        else:
                            self.status_text.value = "Execution failed"
                            self.status_text.color = ft.Colors.RED
                    else:
                        self.status_text.value = "Compilation failed"
                        self.status_text.color = ft.Colors.RED
                    
                    self.status_text.update()
                    close_overlay()
                    
                    # Clean up temp files (only keep .vcd)
                    try:
                        if os.path.exists(temp_dir):
                            for filename in os.listdir(temp_dir):
                                if not filename.endswith('.vcd'):
                                    try:
                                        os.remove(os.path.join(temp_dir, filename))
                                    except:
                                        pass
                    except:
                        pass
                
                self.app.page.run_thread(update_ui)
                
            except Exception as e:
                def show_error():
                    self.app.show_snackbar(f"Test exception: {str(e)}", ft.Colors.RED)
                    self.status_text.value = "Test failed"
                    self.status_text.color = ft.Colors.RED
                    self.status_text.update()
                    close_overlay()
                self.app.page.run_thread(show_error)
        
        # Start background thread to run test
        threading.Thread(target=run_test_thread, daemon=True).start()
    
    def _extract_input_output_signals(self, testbench: str) -> tuple:
        """Extract input and output signal names from testbench
        
        Returns:
            (input_signals, output_signals) - two lists
        """
        input_signals = []
        output_signals = []
        
        # Method 1: Identify from reg/wire definitions
        # In testbench, inputs are usually reg, outputs are usually wire
        for match in re.finditer(r'\b(reg)\s+(?:\[.*?\])?\s*(\w+)', testbench):
            sig = match.group(2)
            if sig not in input_signals:
                input_signals.append(sig)
        
        for match in re.finditer(r'\b(wire)\s+(?:\[.*?\])?\s*(\w+)', testbench):
            sig = match.group(2)
            if sig not in output_signals:
                output_signals.append(sig)
        
        # Method 2: If not found, extract from $display
        # Assume last signal is output (common pattern)
        if not input_signals and not output_signals:
            # Match $display statements
            pattern = r'\$display\s*\([^)]*"[^"]*"\s*,\s*([^)]+)\)'
            for match in re.finditer(pattern, testbench):
                # Extract argument list
                args_str = match.group(1)
                # Split arguments
                args = [arg.strip() for arg in args_str.split(',')]
                # Exclude $time
                signal_args = [arg for arg in args if not arg.startswith('$')]
                # All except last are inputs, last is output
                if len(signal_args) >= 2:
                    input_signals = signal_args[:-1]
                    output_signals = [signal_args[-1]]
        
        return input_signals, output_signals
    
    def _show_test_result_dialog(self, student_result: ExecutionResult, ref_result: ExecutionResult, testbench: str):
        """Show test result dialog (display waveform)"""
        # Extract all signals
        all_signals = self._extract_all_signals(ref_result.output or student_result.output)
        # Extract input and output signals from testbench
        input_signals, output_signals = self._extract_input_output_signals(testbench)
        
        # Use result_analyzer to analyze results
        if ref_result.output and student_result.output:
            analysis = result_analyzer.analyze_from_display(
                ref_result.output,
                student_result.output,
                output_signals
            )
        else:
            analysis = None
        
        # Build dialog content
        content_controls = []
        
        # Compilation status
        if not student_result.compile_success:
            content_controls.extend([
                ft.Text("Compilation Failed", size=18, color=ft.Colors.RED, weight=ft.FontWeight.BOLD),
                ft.Text(student_result.error or "Unknown error", selectable=True),
            ])
        else:
            if analysis and analysis.success and analysis.comparisons:
                # Organize waveform data by signal
                signal_data = self._organize_waveform_data(analysis.comparisons, all_signals, input_signals, output_signals)
                
                # Draw complete waveform (all signals together)
                waveform_container = self._build_combined_waveform(
                    signal_data, input_signals, output_signals
                )
                content_controls.append(waveform_container)
            else:
                # Display raw output
                content_controls.extend([
                    ft.Text("Reference Output:", weight=ft.FontWeight.BOLD),
                    ft.Text(ref_result.output or "(no output)", selectable=True, size=12),
                    ft.Divider(),
                    ft.Text("Student Output:", weight=ft.FontWeight.BOLD),
                    ft.Text(student_result.output or "(no output)", selectable=True, size=12),
                ])
                if student_result.error:
                    content_controls.extend([
                        ft.Text("Error Message:", weight=ft.FontWeight.BOLD, color=ft.Colors.RED),
                        ft.Text(student_result.error, selectable=True, color=ft.Colors.RED),
                    ])
        
        # Create dialog
        def close_dialog(e):
            dialog.open = False
            self.app.page.update()
        
        content = ft.Column(content_controls, scroll=ft.ScrollMode.AUTO, height=500, width=750)
        
        dialog = ft.AlertDialog(
            title=ft.Text("Waveform"),
            content=content,
            actions=[
                ft.TextButton("Close", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.app.page.overlay.append(dialog)
        dialog.open = True
        self.app.page.update()
    
    def _organize_waveform_data(self, comparisons, all_signals, input_signals, output_signals):
        """Organize comparison data into waveform data by signal"""
        signal_data = {}
        
        for sig in all_signals:
            signal_data[sig] = []
            for comp in comparisons:
                time = comp.time
                val = comp.signal_values.get(sig, "0")
                
                # For input signals, expected and actual are the same (both use signal_values)
                if sig in input_signals:
                    expected = val
                    actual = val
                    match = True
                else:
                    # For output signals, get expected and actual values separately
                    expected = comp.expected_outputs.get(sig, val) if hasattr(comp, 'expected_outputs') else val
                    actual = comp.actual_outputs.get(sig, val) if hasattr(comp, 'actual_outputs') else val
                    match = comp.match if hasattr(comp, 'match') else True
                
                signal_data[sig].append({
                    'time': time,
                    'value': val,
                    'expected': expected,
                    'actual': actual,
                    'match': match
                })
        
        return signal_data
    
    def _build_combined_waveform(self, signal_data: dict, input_signals: list, output_signals: list) -> ft.Control:
        """Build complete waveform (all signals together)"""
        if not signal_data:
            return ft.Container()
        
        # Get first signal's data to calculate time range
        first_sig_data = None
        for sig_data in signal_data.values():
            if sig_data:
                first_sig_data = sig_data
                break
        
        if not first_sig_data:
            return ft.Container()
        
        # Calculate total time range
        max_time = max(d['time'] for d in first_sig_data)
        min_time = min(d['time'] for d in first_sig_data)
        time_range = max(1, max_time - min_time)
        
        # Waveform width
        wave_width = 550
        time_scale = wave_width / time_range
        
        # Collect all signals to display (ensure all have data)
        all_display_signals = []
        
        # Display input signals first
        for sig_name in input_signals:
            if sig_name in signal_data and signal_data[sig_name]:
                all_display_signals.append({'name': sig_name, 'type': 'input'})
        
        # Then display output signals
        for sig_name in output_signals:
            if sig_name in signal_data and signal_data[sig_name]:
                all_display_signals.append({'name': sig_name, 'type': 'output'})
        
        if not all_display_signals:
            return ft.Container(content=ft.Text("No signal data"))
        
        # Build a row for each signal
        signal_rows = []
        row_height = 50  # Height of each signal row
        
        for i, sig_info in enumerate(all_display_signals):
            sig_name = sig_info['name']
            sig_type = sig_info['type']
            y_position = i * row_height
            data = signal_data[sig_name]
            
            if sig_type == 'input':
                # Input signals draw one waveform (black) - use actual as input value (expected and actual are same for inputs)
                segments = self._build_signal_waveform(
                    data, min_time, time_scale, 'actual', ft.Colors.BLACK, y_position + 10
                )
                label_text = sig_name
            else:
                # Output signals draw two waveforms: expected (blue) and actual (green)
                expected_segments = self._build_signal_waveform(
                    data, min_time, time_scale, 'expected', ft.Colors.BLUE, y_position + 5
                )
                actual_segments = self._build_signal_waveform(
                    data, min_time, time_scale, 'actual', ft.Colors.GREEN, y_position + 25
                )
                segments = expected_segments + actual_segments
                label_text = f"{sig_name} (exp/act)"
            
            signal_rows.append({
                'name': label_text,
                'y': y_position,
                'height': row_height,
                'segments': segments,
                'is_output': sig_type == 'output'
            })
        
        total_height = len(signal_rows) * row_height
        
        # Build waveform area - use Stack to place all waveform segments
        all_segments = []
        for row in signal_rows:
            all_segments.extend(row['segments'])
        
        # Add separator lines
        for i in range(1, len(signal_rows)):
            sep_y = i * row_height
            separator = ft.Container(
                width=wave_width + 30,
                height=1,
                bgcolor=ft.Colors.GREY_200,
                margin=ft.margin.only(left=0, top=sep_y),
            )
            all_segments.append(separator)
        
        # Time axis baseline
        baseline = ft.Container(
            width=wave_width + 30,
            height=1,
            bgcolor=ft.Colors.GREY_400,
            margin=ft.margin.only(left=0, top=total_height - 5),
        )
        all_segments.append(baseline)
        
        # Waveform Stack
        waveform_stack = ft.Stack(
            all_segments,
            width=wave_width + 30,
            height=total_height,
        )
        
        # Build signal labels - use fixed-height Container for alignment
        signal_labels = []
        for row in signal_rows:
            label_color = ft.Colors.BLUE if row['is_output'] else ft.Colors.BLACK
            signal_labels.append(
                ft.Container(
                    content=ft.Text(
                        row['name'], 
                        size=11, 
                        color=label_color, 
                        weight=ft.FontWeight.BOLD
                    ),
                    height=row_height,
                    alignment=ft.alignment.Alignment(-1, 0),  # left align, vertical center
                    width=110,
                )
            )
        
        # Time axis labels
        time_labels = []
        for point in first_sig_data:
            time = point['time']
            x = int((time - min_time) * time_scale)
            time_labels.append(
                ft.Container(
                    content=ft.Text(str(time), size=9, color=ft.Colors.GREY),
                    margin=ft.margin.only(left=x - 8),
                )
            )
        
        # Legend
        legend = ft.Row([
            ft.Container(width=15, height=3, bgcolor=ft.Colors.BLACK),
            ft.Text("Input", size=10),
            ft.Container(width=15, height=0),
            ft.Container(width=15, height=3, bgcolor=ft.Colors.BLUE),
            ft.Text("Expected", size=10, color=ft.Colors.BLUE),
            ft.Container(width=15, height=0),
            ft.Container(width=15, height=3, bgcolor=ft.Colors.GREEN),
            ft.Text("Actual", size=10, color=ft.Colors.GREEN),
        ], spacing=5)
        
        # Return complete waveform
        return ft.Container(
            content=ft.Column([
                # Legend
                legend,
                ft.Divider(height=1),
                # Waveform main body
                ft.Row([
                    # Signal labels column - use Column for vertical alignment
                    ft.Column(
                        signal_labels, 
                        spacing=0, 
                        width=110,
                        height=total_height,
                    ),
                    # Waveform area
                    ft.Column([
                        waveform_stack,
                        # Time labels
                        ft.Row(time_labels, spacing=0),
                    ], spacing=0),
                ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.START),
            ]),
            padding=10,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
        )
    
    def _build_signal_waveform(self, data: list, min_time: int, time_scale: float, 
                                value_key: str, color: str, y_base: int) -> list:
        """Build waveform segment for single signal"""
        segments = []
        prev_x = 0
        prev_val = None
        
        for i, point in enumerate(data):
            time = point['time']
            val = point.get(value_key, point.get('value', '0'))
            
            # Calculate x position
            x = int((time - min_time) * time_scale)
            
            if i == 0:
                prev_x = x
                prev_val = val
                continue
            
            # Draw line segment from previous point to current point
            width = max(2, x - prev_x)
            
            # Convert value to logic level (0=low, 1=high, 2=unknown)
            val_num = self._parse_logic_value(prev_val)
            
            # Waveform height position (high level on top, low level on bottom)
            if val_num == 1:
                y_offset = y_base  # high level
            elif val_num == 0:
                y_offset = y_base + 12  # low level
            else:
                y_offset = y_base + 6  # intermediate state
            
            # Create horizontal waveform segment
            segment = ft.Container(
                width=width,
                height=2 if val_num != 2 else 6,
                bgcolor=color,
                margin=ft.margin.only(left=prev_x, top=y_offset),
            )
            segments.append(segment)
            
            # Add vertical transition line (if value changes)
            if prev_val != val:
                y1 = y_base if self._parse_logic_value(prev_val) == 1 else y_base + 12
                y2 = y_base if self._parse_logic_value(val) == 1 else y_base + 12
                
                jump = ft.Container(
                    width=1,
                    height=abs(y2 - y1) + 2,
                    bgcolor=color,
                    margin=ft.margin.only(left=x, top=min(y1, y2)),
                )
                segments.append(jump)
            
            prev_x = x
            prev_val = val
        
        # Add last point
        if data:
            last_val = data[-1].get(value_key, data[-1].get('value', '0'))
            val_num = self._parse_logic_value(last_val)
            y_offset = y_base if val_num == 1 else (y_base + 12 if val_num == 0 else y_base + 6)
            
            last_segment = ft.Container(
                width=15,
                height=2 if val_num != 2 else 6,
                bgcolor=color,
                margin=ft.margin.only(left=prev_x, top=y_offset),
            )
            segments.append(last_segment)
        
        return segments
    
    def _parse_logic_value(self, val: str) -> int:
        """Parse logic value to number (0=low, 1=high, 2=unknown/other)"""
        if val in ['0', "1'b0", "1'h0"]:
            return 0
        elif val in ['1', "1'b1", "1'h1"]:
            return 1
        elif val in ['x', 'X', 'z', 'Z', '?']:
            return 2
        else:
            # Try to parse number
            try:
                if val.startswith("1'b"):
                    return int(val[3:])
                elif val.startswith("1'h"):
                    return int(val[3:], 16) % 2
                else:
                    return int(val) % 2
            except:
                return 2
    
    def _extract_all_signals(self, output: str) -> list:
        """Extract all signal names from output"""
        signals = []
        for line in output.split('\n'):
            if 'time=' in line or 't=' in line:
                # Match name=value pairs
                for match in re.finditer(r'(\w+)=([\w\'b\d]+)', line):
                    sig = match.group(1)
                    if sig not in ['time', 't'] and sig not in signals:
                        signals.append(sig)
        return signals
    
    def _save_test_result(self, exec_result: ExecutionResult):
        """Save test results (using ID naming, organized by question subfolder)"""
        result_data = {
            "test_time": datetime.now().isoformat(),
            "question_id": self.question_id,
            "compile_success": exec_result.compile_success,
            "run_success": exec_result.run_success,
            "output": exec_result.output,
            "error": exec_result.error,
            "vcd_file": exec_result.vcd_file,
        }
        
        # Use ID as subdirectory
        question_dir = os.path.join(SUBMISSIONS_DIR, f"week{self.week}", self.question_id)
        os.makedirs(question_dir, exist_ok=True)
        
        result_file = os.path.join(question_dir, "result.json")
        
        try:
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save test results: {e}")
    
    def _on_save_and_continue(self, e):
        """Save and continue button click"""
        if self._save_code():
            # Mark current question as completed
            self._update_progress(status="completed")
            
            total = len(self.app.drawn_questions)
            
            if self.question_index + 1 < total:
                # There is a next question
                self.app.navigate_to_question(self.question_index + 1)
            else:
                # Week completed
                self._mark_week_completed()
                self.app.show_snackbar("Week completed! Please generate report.", ft.Colors.GREEN)
                self._show_report_dialog()
    
    def _on_prev_question(self, e):
        """Previous question button click"""
        if self.question_index > 0:
            self.app.navigate_to_question(self.question_index - 1)
    
    def _mark_week_completed(self):
        """Mark week as completed (iterate through all question subfolders)"""
        week_dir = os.path.join(SUBMISSIONS_DIR, f"week{self.week}")
        
        if not os.path.exists(week_dir):
            return
            
        try:
            # Iterate through all question subfolders
            for qid in os.listdir(week_dir):
                q_dir = os.path.join(week_dir, qid)
                if not os.path.isdir(q_dir):
                    continue
                    
                progress_file = os.path.join(q_dir, "progress.json")
                if os.path.exists(progress_file):
                    try:
                        with open(progress_file, 'r', encoding='utf-8') as f:
                            progress_data = json.load(f)
                        
                        if progress_data.get("status") != "completed":
                            progress_data["status"] = "completed"
                            progress_data["completed_at"] = datetime.now().isoformat()
                            
                            with open(progress_file, 'w', encoding='utf-8') as f:
                                json.dump(progress_data, f, ensure_ascii=False, indent=2)
                    except Exception as e:
                        print(f"Failed to mark question {qid} as completed: {e}")
        except Exception as e:
            print(f"Failed to mark completion status: {e}")
    
    def _show_report_dialog(self):
        """Show generate report dialog"""
        from core.report_generator import report_generator
        
        def generate_report(e):
            dialog.open = False
            self.app.page.update()
            
            # Generate report
            report_path = report_generator.generate_week_report(self.week)
            
            if report_path:
                self.app.show_snackbar(f"Report generated: {report_path}", ft.Colors.GREEN)
                self._show_open_report_dialog(report_path)
            else:
                self.app.show_snackbar("Report generation failed", ft.Colors.RED)
        
        def close_dialog(e):
            dialog.open = False
            self.app.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Generate Report"),
            content=ft.Text("All questions for this week are completed. Generate report?"),
            actions=[
                ft.TextButton("Later", on_click=close_dialog),
                ft.ElevatedButton("Generate", on_click=generate_report),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.app.page.overlay.append(dialog)
        dialog.open = True
        self.app.page.update()
    
    def _show_open_report_dialog(self, report_path: str):
        """Show open report dialog, return to question selection after close"""
        import subprocess
        import sys
        
        def open_folder(e):
            folder = os.path.dirname(report_path)
            try:
                # Choose open method based on platform
                if sys.platform == 'win32':
                    subprocess.run(['explorer', folder])
                elif sys.platform == 'darwin':
                    subprocess.run(['open', folder])
                else:
                    subprocess.run(['xdg-open', folder])
            except Exception as ex:
                self.app.show_snackbar(f"Cannot open folder: {ex}", ft.Colors.RED)
            
            dialog.open = False
            self.app.page.update()
            # Return to question selection interface
            self.app.show_week_selector()
        
        def close(e):
            dialog.open = False
            self.app.page.update()
            # 返回题目选择界面
            self.app.show_week_selector()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Report Generated"),
            content=ft.Text(f"Report path:\n{report_path}"),
            actions=[
                ft.TextButton("Close", on_click=close),
                ft.ElevatedButton("Open Folder", on_click=open_folder),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.app.page.overlay.append(dialog)
        dialog.open = True
        self.app.page.update()
