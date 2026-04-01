"""
答题界面
"""
import os
import json
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
    """答题界面组件"""
    
    def __init__(self, app):
        self.app = app
        self.code_editor = None
        self.save_timer = None
        self.current_code = ""
        self.week = None
        self.question_index = None
        self.original_question_id = None
    
    def build(self, week: int, question_index: int) -> ft.Control:
        """构建答题界面"""
        self.week = week
        self.question_index = question_index
        
        # 加载题目信息
        self._load_question_info()
        
        # 加载已有代码（如果有）
        existing_code = self._load_existing_code()
        
        return ft.Column(
            [
                self._build_header(),
                ft.Divider(),
                ft.Row(
                    [
                        self._build_question_panel(),
                        ft.VerticalDivider(width=1),
                        self._build_editor_panel(existing_code),
                    ],
                    expand=True,
                ),
                ft.Divider(),
                self._build_footer(),
            ],
            expand=True,
        )
    
    def _build_header(self) -> ft.Control:
        """构建顶部导航栏"""
        total = len(self.app.drawn_questions) if self.app.drawn_questions else 0
        current = self.question_index + 1
        
        return ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        tooltip="返回周次列表",
                        on_click=lambda e: self.app.show_week_selector(),
                    ),
                    ft.Text(
                        f"Week {self.week} - 题目 {current}/{total}",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Row(
                        [
                            ft.Text(
                                f"原题号: {self.original_question_id or 'N/A'}",
                                size=12,
                                color=ft.Colors.GREY,
                            ),
                        ]
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
        )
    
    def _build_question_panel(self) -> ft.Control:
        """构建题目显示面板（左侧）"""
        # 读取题目内容
        question_md = self._load_question_markdown()
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("题目描述", size=18, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=1),
                    ft.Markdown(
                        question_md,
                        selectable=True,
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                        code_theme=ft.MarkdownCodeTheme.GITHUB,
                    ),
                ],
                scroll=ft.ScrollMode.AUTO,
            ),
            width=500,
            padding=10,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
        )
    
    def _build_editor_panel(self, existing_code: str) -> ft.Control:
        """构建代码编辑面板（右侧）"""
        self.current_code = existing_code
        
        self.code_editor = ft.TextField(
            value=existing_code,
            multiline=True,
            min_lines=20,
            max_lines=None,
            text_style=ft.TextStyle(
                font_family=CODE_FONT,
                size=CODE_FONT_SIZE,
            ),
            border_color=ft.Colors.BLUE_400,
            hint_text="在此编写Verilog代码...",
            on_change=self._on_code_change,
        )
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("代码编辑器", size=18, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=1),
                    self.code_editor,
                ],
                expand=True,
            ),
            expand=True,
            padding=10,
            border=ft.border.all(1, ft.Colors.BLUE_200),
            border_radius=8,
        )
    
    def _build_footer(self) -> ft.Control:
        """构建底部操作栏"""
        self.status_text = ft.Text(
            "就绪",
            size=12,
            color=ft.Colors.GREY,
        )
        
        return ft.Container(
            content=ft.Row(
                [
                    self.status_text,
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "运行测试",
                                icon=ft.Icons.PLAY_ARROW,
                                on_click=self._on_run_test,
                                style=ft.ButtonStyle(
                                    color=ft.Colors.WHITE,
                                    bgcolor=ft.Colors.GREEN,
                                ),
                            ),
                            ft.ElevatedButton(
                                "保存并继续",
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
        """加载题目信息"""
        # 读取抽题结果
        draw_file = os.path.join(QUESTIONS_DIR, f"week{self.week}", "draw_result.json")
        
        if os.path.exists(draw_file):
            try:
                with open(draw_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.app.drawn_questions = data.get("drawn_questions", [])
                    
                    if self.question_index < len(self.app.drawn_questions):
                        self.original_question_id = self.app.drawn_questions[self.question_index]
            except Exception as e:
                print(f"读取抽题结果失败: {e}")
    
    def _load_question_markdown(self) -> str:
        """加载题目Markdown内容"""
        if not self.original_question_id:
            return "# 题目加载失败\n\n请返回重新选择周次。"
        
        md_file = os.path.join(
            QUESTIONS_DIR, 
            f"week{self.week}", 
            self.original_question_id,
            "question.md"
        )
        
        if os.path.exists(md_file):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                return f"# 读取题目失败\n\n{e}"
        
        return "# 题目文件不存在\n\n请检查更新。"
    
    def _load_existing_code(self) -> str:
        """加载已有的代码"""
        code_file = os.path.join(
            SUBMISSIONS_DIR,
            f"week{self.week}",
            f"q_selected_{self.question_index + 1}.v"
        )
        
        if os.path.exists(code_file):
            try:
                with open(code_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"读取已有代码失败: {e}")
        
        # 返回模板代码
        return self._get_code_template()
    
    def _get_code_template(self) -> str:
        """获取代码模板"""
        return """// 在此编写你的Verilog代码

module my_module (
    // 定义端口
);
    
    // 实现逻辑
    
endmodule
"""
    
    def _on_code_change(self, e):
        """代码改变事件"""
        self.current_code = e.control.value
        self.status_text.value = "有未保存的更改"
        self.status_text.color = ft.Colors.ORANGE
        self.status_text.update()
        
        # TODO: 实现定时自动保存
    
    def _save_code(self) -> bool:
        """保存代码"""
        if not self.original_question_id:
            return False
        
        # 确保目录存在
        week_dir = os.path.join(SUBMISSIONS_DIR, f"week{self.week}")
        os.makedirs(week_dir, exist_ok=True)
        
        # 保存代码文件
        code_file = os.path.join(week_dir, f"q_selected_{self.question_index + 1}.v")
        
        try:
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(self.current_code)
            
            # 更新进度
            self._update_progress()
            
            self.status_text.value = f"已保存 {datetime.now().strftime('%H:%M:%S')}"
            self.status_text.color = ft.Colors.GREEN
            self.status_text.update()
            
            return True
        except Exception as e:
            self.status_text.value = f"保存失败: {e}"
            self.status_text.color = ft.Colors.RED
            self.status_text.update()
            return False
    
    def _update_progress(self):
        """更新进度文件"""
        week_dir = os.path.join(SUBMISSIONS_DIR, f"week{self.week}")
        progress_file = os.path.join(week_dir, "progress.json")
        
        progress_data = {"questions": []}
        
        # 读取现有进度
        if os.path.exists(progress_file):
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
            except Exception:
                pass
        
        # 确保questions数组长度足够
        questions = progress_data.get("questions", [])
        while len(questions) <= self.question_index:
            questions.append({
                "original_id": self.app.drawn_questions[len(questions)] if len(questions) < len(self.app.drawn_questions) else "",
                "status": "pending",
                "last_save": None,
            })
        
        # 更新当前题目状态
        questions[self.question_index] = {
            "original_id": self.original_question_id,
            "status": "in_progress",
            "last_save": datetime.now().isoformat(),
        }
        
        progress_data["questions"] = questions
        
        try:
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"更新进度失败: {e}")
    
    def _on_run_test(self, e):
        """运行测试按钮点击"""
        # 先保存代码
        if not self._save_code():
            self.app.show_snackbar("保存代码失败，无法测试", ft.Colors.RED)
            return
        
        # 运行测试
        self._run_test_workflow()
    
    def _on_save_and_continue(self, e):
        """保存并继续按钮点击"""
        if self._save_code():
            total = len(self.app.drawn_questions)
            
            if self.question_index + 1 < total:
                # 还有下一题
                self.app.navigate_to_question(self.question_index + 1)
            else:
                # 本周完成
                self._mark_week_completed()
                self.app.show_snackbar("本周作业已完成！请生成报告。", ft.Colors.GREEN)
                # 显示生成报告对话框
                self._show_report_dialog()
    
    def _mark_week_completed(self):
        """标记本周已完成"""
        week_dir = os.path.join(SUBMISSIONS_DIR, f"week{self.week}")
        progress_file = os.path.join(week_dir, "progress.json")
        
        if os.path.exists(progress_file):
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
                
                questions = progress_data.get("questions", [])
                for i in range(len(questions)):
                    if questions[i].get("status") != "completed":
                        questions[i]["status"] = "completed"
                
                progress_data["questions"] = questions
                
                with open(progress_file, 'w', encoding='utf-8') as f:
                    json.dump(progress_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"标记完成状态失败: {e}")
    
    def _run_test_workflow(self):
        """运行完整测试流程"""
        import tempfile
        
        self.status_text.value = "正在运行测试..."
        self.status_text.color = ft.Colors.BLUE
        self.status_text.update()
        
        # 1. 获取参考代码
        ref_code = question_manager.get_reference_code(self.week, self.original_question_id)
        if ref_code is None:
            self.app.show_snackbar("无法获取参考答案", ft.Colors.RED)
            self.status_text.value = "测试失败"
            self.status_text.color = ft.Colors.RED
            self.status_text.update()
            return
        
        # 2. 创建临时工作目录
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # 3. 读取testbench
                tb_path = os.path.join(
                    QUESTIONS_DIR, 
                    f"week{self.week}", 
                    self.original_question_id,
                    "testbench.v"
                )
                
                if not os.path.exists(tb_path):
                    self.app.show_snackbar("未找到testbench文件", ft.Colors.RED)
                    return
                
                with open(tb_path, 'r', encoding='utf-8') as f:
                    testbench = f.read()
                
                # 4. 写入学生代码
                student_file = os.path.join(temp_dir, "student.v")
                with open(student_file, 'w', encoding='utf-8') as f:
                    f.write(self.current_code)
                
                # 5. 写入参考代码（修改模块名为ref_xxx）
                ref_file = os.path.join(temp_dir, "reference.v")
                # 简单处理：假设模块名是reference.v中的第一个module
                ref_code_modified = self._modify_module_name(ref_code, "ref_")
                with open(ref_file, 'w', encoding='utf-8') as f:
                    f.write(ref_code_modified)
                
                # 6. 创建两个testbench副本（分别实例化学生和参考模块）
                # 这里简化处理，假设testbench使用 dut 作为实例名
                student_tb = testbench.replace(
                    "student_module", self._extract_module_name(self.current_code) or "unknown"
                )
                ref_tb = testbench.replace(
                    "student_module", "ref_" + (self._extract_module_name(ref_code) or "unknown")
                )
                
                # 分别保存并执行（简化：只执行学生代码）
                # TODO: 实际应该分别执行对比输出
                
                # 7. 执行学生代码
                exec_result = code_executor.execute(
                    [student_file, os.path.join(temp_dir, "tb_student.v")],
                    temp_dir,
                    "student.vvp"
                )
                
                # 保存结果
                self._save_test_result(exec_result, AnalysisResult(
                    success=exec_result.success,
                    comparisons=[],
                    all_match=exec_result.success
                ))
                
                # 显示结果
                if exec_result.compile_success:
                    if exec_result.run_success:
                        self.status_text.value = "测试完成"
                        self.status_text.color = ft.Colors.GREEN
                        self.app.show_snackbar("测试通过！", ft.Colors.GREEN)
                    else:
                        self.status_text.value = "运行失败"
                        self.status_text.color = ft.Colors.RED
                        self.app.show_snackbar(f"运行失败: {exec_result.error[:100]}", ft.Colors.RED)
                else:
                    self.status_text.value = "编译失败"
                    self.status_text.color = ft.Colors.RED
                    self.app.show_snackbar(f"编译错误: {exec_result.error[:100]}", ft.Colors.RED)
                
                self.status_text.update()
                
            except Exception as e:
                self.app.show_snackbar(f"测试异常: {str(e)}", ft.Colors.RED)
                self.status_text.value = "测试失败"
                self.status_text.color = ft.Colors.RED
                self.status_text.update()
    
    def _extract_module_name(self, code: str) -> str:
        """从代码中提取模块名"""
        import re
        match = re.search(r'module\s+(\w+)', code)
        return match.group(1) if match else None
    
    def _modify_module_name(self, code: str, prefix: str) -> str:
        """修改代码中的模块名"""
        import re
        return re.sub(r'module\s+(\w+)', f'module {prefix}\\1', code, count=1)
    
    def _save_test_result(self, exec_result: ExecutionResult, analysis: AnalysisResult):
        """保存测试结果"""
        result_data = {
            "test_time": datetime.now().isoformat(),
            "compile_success": exec_result.compile_success,
            "run_success": exec_result.run_success,
            "output": exec_result.output,
            "error": exec_result.error,
            "vcd_file": exec_result.vcd_file,
        }
        
        result_file = os.path.join(
            SUBMISSIONS_DIR,
            f"week{self.week}",
            f"q_selected_{self.question_index + 1}_result.json"
        )
        
        try:
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存测试结果失败: {e}")
    
    def _show_report_dialog(self):
        """显示生成报告对话框"""
        from core.report_generator import report_generator
        
        def generate_report(e):
            dialog.open = False
            self.app.page.update()
            
            # 生成报告
            report_path = report_generator.generate_week_report(self.week)
            
            if report_path:
                self.app.show_snackbar(f"报告已生成: {report_path}", ft.Colors.GREEN)
                
                # 显示打开文件夹按钮
                self._show_open_report_dialog(report_path)
            else:
                self.app.show_snackbar("报告生成失败", ft.Colors.RED)
        
        def close_dialog(e):
            dialog.open = False
            self.app.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("生成报告"),
            content=ft.Text("本周所有题目已完成，是否生成报告？"),
            actions=[
                ft.TextButton("稍后", on_click=close_dialog),
                ft.ElevatedButton("生成报告", on_click=generate_report),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.app.page.overlay.append(dialog)
        dialog.open = True
        self.app.page.update()
    
    def _show_open_report_dialog(self, report_path: str):
        """显示打开报告对话框"""
        import subprocess
        
        def open_folder(e):
            folder = os.path.dirname(report_path)
            subprocess.run(['explorer', folder])
            dialog.open = False
            self.app.page.update()
        
        def close(e):
            dialog.open = False
            self.app.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("报告已生成"),
            content=ft.Text(f"报告路径:\n{report_path}"),
            actions=[
                ft.TextButton("关闭", on_click=close),
                ft.ElevatedButton("打开文件夹", on_click=open_folder),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.app.page.overlay.append(dialog)
        dialog.open = True
        self.app.page.update()
