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
    """答题界面组件"""
    
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
        """构建答题界面"""
        self.week = week
        self.question_index = question_index
        
        # 加载题目信息
        self._load_question_info()
        
        if not self.question_id:
            return ft.Column([
                ft.Text("题目加载失败", size=24, color=ft.Colors.RED),
                ft.ElevatedButton("返回", on_click=lambda e: self.app.show_week_selector())
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
                # 题目描述
                self._build_question_panel(),
                ft.Divider(height=1),
                # 代码编辑器
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
                        tooltip="返回周次列表",
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
    
    def _build_question_panel(self) -> ft.Control:
        """构建题目显示面板"""
        question_md = self._load_question_markdown()
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("题目描述", size=16, weight=ft.FontWeight.BOLD),
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
        """构建代码编辑面板"""
        self.current_code = existing_code
        
        # 自动保存函数（当焦点移出时）
        def on_blur_save(e):
            """焦点移出时自动保存"""
            if self._save_code():
                print(f"自动保存: {self.question_id}.v")
        
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
            hint_text="在此编写Verilog代码...",
            on_change=self._on_code_change,
            on_blur=on_blur_save,  # 焦点移出时自动保存
            expand=True,  # 让TextField填充宽度
        )
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("代码编辑器", size=16, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=1),
                    self.code_editor,
                ],
                spacing=5,
            ),
            padding=10,
            border=ft.border.all(1, ft.Colors.BLUE_200),
            border_radius=8,
        )
    
    def _build_testbench_panel(self, testbench_code: str) -> ft.Control:
        """构建testbench显示面板（只读）"""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("测试平台 (Testbench)", size=16, weight=ft.FontWeight.BOLD),
                    ft.Divider(height=1),
                    ft.TextField(
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
                        expand=True,  # 让TextField填充宽度
                    ),
                ],
                spacing=5,
            ),
            padding=10,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
        )
    
    def _load_testbench_code(self) -> str:
        """加载testbench代码"""
        if not self.question_id:
            return "// 无法加载testbench"
        
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
                    # 统一换行符为 \n，避免 Windows \r\n 导致的多余空行
                    return content.replace('\r\n', '\n')
            except Exception as e:
                return f"// 读取testbench失败: {e}"
        
        return "// testbench文件不存在"
    
    def _build_footer(self) -> ft.Control:
        """构建底部操作栏"""
        self.status_text = ft.Text(
            "就绪",
            size=12,
            color=ft.Colors.GREY,
        )
        
        # 判断是否是第一题
        is_first = self.question_index == 0
        
        return ft.Container(
            content=ft.Row(
                [
                    self.status_text,
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "上一题",
                                icon=ft.Icons.ARROW_BACK,
                                on_click=self._on_prev_question,
                                disabled=is_first,
                            ),
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
        """加载题目信息（包括ID、folder、title）"""
        # 读取抽题结果
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
                print(f"读取抽题结果失败: {e}")
    
    def _load_question_markdown(self) -> str:
        """加载题目Markdown内容（使用ID作为目录名）"""
        if not self.question_id:
            return "# 题目加载失败\n\n请返回重新选择周次。"
        
        # 使用ID作为子目录名
        md_file = os.path.join(
            QUESTIONS_DIR, 
            f"week{self.week}", 
            self.question_id,  # 使用ID
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
        """加载已有的代码（使用ID命名，按题目子文件夹组织）"""
        if not self.question_id:
            return self._get_code_template()
        
        # 使用ID作为子目录和文件名
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
                    # 统一换行符为 \n，避免 Windows \r\n 导致的多余空行
                    return content.replace('\r\n', '\n')
            except Exception as e:
                print(f"读取已有代码失败: {e}")
        
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
        self._update_code_status(e.control.value)
    
    def _update_code_status(self, value: str):
        """更新代码状态"""
        self.current_code = value
        self.status_text.value = "有未保存的更改"
        self.status_text.color = ft.Colors.ORANGE
        self.status_text.update()
    
    def _save_code(self) -> bool:
        """保存代码（使用ID命名，按题目子文件夹组织）"""
        if not self.question_id:
            return False
        
        # 确保目录存在：submissions/weekX/question_id/
        question_dir = os.path.join(SUBMISSIONS_DIR, f"week{self.week}", self.question_id)
        os.makedirs(question_dir, exist_ok=True)
        
        # 保存代码文件
        code_file = os.path.join(question_dir, f"{self.question_id}.v")
        
        try:
            # 保存时统一使用 \n 作为换行符
            normalized_code = self.current_code.replace('\r\n', '\n').replace('\r', '\n')
            with open(code_file, 'w', encoding='utf-8', newline='\n') as f:
                f.write(normalized_code)
            
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
        """更新进度文件（使用ID记录，保存在题目子文件夹中）"""
        question_dir = os.path.join(SUBMISSIONS_DIR, f"week{self.week}", self.question_id)
        os.makedirs(question_dir, exist_ok=True)
        
        progress_file = os.path.join(question_dir, "progress.json")
        
        progress_data = {}
        
        # 读取现有进度
        if os.path.exists(progress_file):
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
            except Exception:
                pass
        
        # 更新当前题目状态
        progress_data.update({
            "question_id": self.question_id,
            "index": self.question_index,
            "title": self.question_info.get('title', '') if self.question_info else '',
            "status": "in_progress",
            "last_save": datetime.now().isoformat(),
        })
        
        try:
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"更新进度失败: {e}")
    
    def _on_run_test(self, e):
        """运行测试按钮点击"""
        if not self._save_code():
            self.app.show_snackbar("保存代码失败，无法测试", ft.Colors.RED)
            return
        
        # 运行测试
        self._run_test_workflow()
    
    def _run_test_workflow(self):
        """运行完整测试流程（临时文件放在submissions对应题目目录下）"""
        import threading
        
        # 显示加载遮罩
        loading_text = ft.Text("正在准备测试环境...", size=16, color=ft.Colors.WHITE)
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
            """更新进度消息（线程安全）"""
            def _update():
                loading_text.value = msg
                self.app.page.update()
            self.app.page.run_thread(_update)
        
        def show_snackbar_safe(text, color):
            """安全显示提示"""
            def _show():
                self.app.show_snackbar(text, color)
            self.app.page.run_thread(_show)
        
        def close_overlay():
            """关闭遮罩"""
            def _close():
                try:
                    if loading_overlay in self.app.page.overlay:
                        self.app.page.overlay.remove(loading_overlay)
                        self.app.page.update()
                except Exception:
                    pass
            self.app.page.run_thread(_close)
        
        def run_test_thread():
            """在后台线程中运行测试"""
            try:
                # 1. 获取参考代码
                update_message("正在获取参考答案...")
                ref_code = question_manager.get_reference_code(self.week, self.question_id)
                
                # 2. 创建临时工作目录
                update_message("正在准备仿真环境...")
                question_dir = os.path.join(SUBMISSIONS_DIR, f"week{self.week}", self.question_id)
                temp_dir = os.path.join(question_dir, "temp")
                os.makedirs(temp_dir, exist_ok=True)
                
                if ref_code is None:
                    show_snackbar_safe("无法获取参考答案", ft.Colors.RED)
                    close_overlay()
                    return
                
                # 3. 读取testbench
                update_message("正在读取测试平台...")
                tb_path = os.path.join(QUESTIONS_DIR, f"week{self.week}", self.question_id, "testbench.v")
                
                if not os.path.exists(tb_path):
                    show_snackbar_safe("未找到testbench文件", ft.Colors.RED)
                    close_overlay()
                    return
                
                with open(tb_path, 'r', encoding='utf-8') as f:
                    testbench = f.read()
                
                # 4. 写入学生代码
                student_file = os.path.join(temp_dir, "student.v")
                with open(student_file, 'w', encoding='utf-8') as f:
                    f.write(self.current_code)
                
                # 5. 写入参考代码
                ref_file = os.path.join(temp_dir, "reference.v")
                with open(ref_file, 'w', encoding='utf-8') as f:
                    f.write(ref_code)
                
                # 6. 执行参考代码测试
                update_message("正在运行参考答案仿真...")
                ref_result = code_executor.execute([ref_file, tb_path], temp_dir, "ref.vvp")
                
                # 7. 执行学生代码测试
                update_message("正在运行学生代码仿真...")
                student_result = code_executor.execute([student_file, tb_path], temp_dir, "student.vvp")
                
                # 8. 保存结果
                update_message("正在保存测试结果...")
                self._save_test_result(student_result)
                
                # 9. 显示结果和更新UI（在主线程中）
                def update_ui():
                    self._show_test_result_dialog(student_result, ref_result, testbench)
                    
                    if student_result.compile_success:
                        if student_result.run_success:
                            self.status_text.value = "测试完成"
                            self.status_text.color = ft.Colors.GREEN
                        else:
                            self.status_text.value = "运行失败"
                            self.status_text.color = ft.Colors.RED
                    else:
                        self.status_text.value = "编译失败"
                        self.status_text.color = ft.Colors.RED
                    
                    self.status_text.update()
                    close_overlay()
                    
                    # 清理临时文件（只保留.vcd）
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
                    self.app.show_snackbar(f"测试异常: {str(e)}", ft.Colors.RED)
                    self.status_text.value = "测试失败"
                    self.status_text.color = ft.Colors.RED
                    self.status_text.update()
                    close_overlay()
                self.app.page.run_thread(show_error)
        
        # 启动后台线程运行测试
        threading.Thread(target=run_test_thread, daemon=True).start()
    
    def _extract_input_output_signals(self, testbench: str) -> tuple:
        """从testbench中提取输入信号和输出信号名
        
        Returns:
            (input_signals, output_signals) - 两个列表
        """
        input_signals = []
        output_signals = []
        
        # 方法1: 从 reg/wire 定义中识别
        # 在testbench中，输入通常是reg，输出通常是wire
        for match in re.finditer(r'\b(reg)\s+(?:\[.*?\])?\s*(\w+)', testbench):
            sig = match.group(2)
            if sig not in input_signals:
                input_signals.append(sig)
        
        for match in re.finditer(r'\b(wire)\s+(?:\[.*?\])?\s*(\w+)', testbench):
            sig = match.group(2)
            if sig not in output_signals:
                output_signals.append(sig)
        
        # 方法2: 如果没找到，从 $display 中提取，
        # 但假设最后一个信号是输出（常见模式）
        if not input_signals and not output_signals:
            # 匹配 $display 语句
            pattern = r'\$display\s*\([^)]*"[^"]*"\s*,\s*([^)]+)\)'
            for match in re.finditer(pattern, testbench):
                # 提取参数列表
                args_str = match.group(1)
                # 分割参数
                args = [arg.strip() for arg in args_str.split(',')]
                # 排除 $time 或 $time
                signal_args = [arg for arg in args if not arg.startswith('$')]
                # 除最后一个外都是输入，最后一个是输出
                if len(signal_args) >= 2:
                    input_signals = signal_args[:-1]
                    output_signals = [signal_args[-1]]
        
        return input_signals, output_signals
    
    def _show_test_result_dialog(self, student_result: ExecutionResult, ref_result: ExecutionResult, testbench: str):
        """显示测试结果对话框（显示波形图）"""
        # 提取所有信号
        all_signals = self._extract_all_signals(ref_result.output or student_result.output)
        # 从testbench中提取输入和输出信号
        input_signals, output_signals = self._extract_input_output_signals(testbench)
        
        # 使用result_analyzer分析结果
        if ref_result.output and student_result.output:
            analysis = result_analyzer.analyze_from_display(
                ref_result.output,
                student_result.output,
                output_signals
            )
        else:
            analysis = None
        
        # 构建对话框内容
        content_controls = []
        
        # 编译状态
        if not student_result.compile_success:
            content_controls.extend([
                ft.Text("编译失败", size=18, color=ft.Colors.RED, weight=ft.FontWeight.BOLD),
                ft.Text(student_result.error or "未知错误", selectable=True),
            ])
        else:
            if analysis and analysis.success and analysis.comparisons:
                # 按信号组织波形数据
                signal_data = self._organize_waveform_data(analysis.comparisons, all_signals, input_signals, output_signals)
                
                # 绘制完整的波形图（所有信号在一起）
                waveform_container = self._build_combined_waveform(
                    signal_data, input_signals, output_signals
                )
                content_controls.append(waveform_container)
            else:
                # 显示原始输出
                content_controls.extend([
                    ft.Text("参考输出:", weight=ft.FontWeight.BOLD),
                    ft.Text(ref_result.output or "(无输出)", selectable=True, size=12),
                    ft.Divider(),
                    ft.Text("学生输出:", weight=ft.FontWeight.BOLD),
                    ft.Text(student_result.output or "(无输出)", selectable=True, size=12),
                ])
                if student_result.error:
                    content_controls.extend([
                        ft.Text("错误信息:", weight=ft.FontWeight.BOLD, color=ft.Colors.RED),
                        ft.Text(student_result.error, selectable=True, color=ft.Colors.RED),
                    ])
        
        # 创建对话框
        def close_dialog(e):
            dialog.open = False
            self.app.page.update()
        
        content = ft.Column(content_controls, scroll=ft.ScrollMode.AUTO, height=500, width=750)
        
        dialog = ft.AlertDialog(
            title=ft.Text("波形图"),
            content=content,
            actions=[
                ft.TextButton("关闭", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.app.page.overlay.append(dialog)
        dialog.open = True
        self.app.page.update()
    
    def _organize_waveform_data(self, comparisons, all_signals, input_signals, output_signals):
        """将对比数据按信号组织成波形数据"""
        signal_data = {}
        
        for sig in all_signals:
            signal_data[sig] = []
            for comp in comparisons:
                time = comp.time
                val = comp.signal_values.get(sig, "0")
                
                # 对于输入信号，期望和实际是一样的（都使用 signal_values 的值）
                if sig in input_signals:
                    expected = val
                    actual = val
                    match = True
                else:
                    # 对于输出信号，分别获取期望和实际值
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
        """构建完整的波形图（所有信号在一起）"""
        if not signal_data:
            return ft.Container()
        
        # 获取第一个信号的数据来计算时间范围
        first_sig_data = None
        for sig_data in signal_data.values():
            if sig_data:
                first_sig_data = sig_data
                break
        
        if not first_sig_data:
            return ft.Container()
        
        # 计算总时间范围
        max_time = max(d['time'] for d in first_sig_data)
        min_time = min(d['time'] for d in first_sig_data)
        time_range = max(1, max_time - min_time)
        
        # 波形图宽度
        wave_width = 550
        time_scale = wave_width / time_range
        
        # 收集所有要显示的信号（确保所有信号都有数据）
        all_display_signals = []
        
        # 先显示输入信号
        for sig_name in input_signals:
            if sig_name in signal_data and signal_data[sig_name]:
                all_display_signals.append({'name': sig_name, 'type': 'input'})
        
        # 再显示输出信号
        for sig_name in output_signals:
            if sig_name in signal_data and signal_data[sig_name]:
                all_display_signals.append({'name': sig_name, 'type': 'output'})
        
        if not all_display_signals:
            return ft.Container(content=ft.Text("无信号数据"))
        
        # 为每个信号构建一行
        signal_rows = []
        row_height = 50  # 每个信号行的高度
        
        for i, sig_info in enumerate(all_display_signals):
            sig_name = sig_info['name']
            sig_type = sig_info['type']
            y_position = i * row_height
            data = signal_data[sig_name]
            
            if sig_type == 'input':
                # 输入信号只画一个波形（黑色）- 使用 actual 作为输入值（输入的期望和实际是一样的）
                segments = self._build_signal_waveform(
                    data, min_time, time_scale, 'actual', ft.Colors.BLACK, y_position + 10
                )
                label_text = sig_name
            else:
                # 输出信号画两个波形：期望（蓝色）和实际（绿色）
                expected_segments = self._build_signal_waveform(
                    data, min_time, time_scale, 'expected', ft.Colors.BLUE, y_position + 5
                )
                actual_segments = self._build_signal_waveform(
                    data, min_time, time_scale, 'actual', ft.Colors.GREEN, y_position + 25
                )
                segments = expected_segments + actual_segments
                label_text = f"{sig_name} (期望/实际)"
            
            signal_rows.append({
                'name': label_text,
                'y': y_position,
                'height': row_height,
                'segments': segments,
                'is_output': sig_type == 'output'
            })
        
        total_height = len(signal_rows) * row_height
        
        # 构建波形区域 - 使用 Stack 放置所有波形段
        all_segments = []
        for row in signal_rows:
            all_segments.extend(row['segments'])
        
        # 添加分隔线
        for i in range(1, len(signal_rows)):
            sep_y = i * row_height
            separator = ft.Container(
                width=wave_width + 30,
                height=1,
                bgcolor=ft.Colors.GREY_200,
                margin=ft.margin.only(left=0, top=sep_y),
            )
            all_segments.append(separator)
        
        # 时间轴基线
        baseline = ft.Container(
            width=wave_width + 30,
            height=1,
            bgcolor=ft.Colors.GREY_400,
            margin=ft.margin.only(left=0, top=total_height - 5),
        )
        all_segments.append(baseline)
        
        # 波形 Stack
        waveform_stack = ft.Stack(
            all_segments,
            width=wave_width + 30,
            height=total_height,
        )
        
        # 构建信号标签 - 使用固定高度的 Container 确保对齐
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
                    alignment=ft.alignment.Alignment(-1, 0),  # 左对齐，垂直居中
                    width=110,
                )
            )
        
        # 时间轴刻度
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
        
        # 图例
        legend = ft.Row([
            ft.Container(width=15, height=3, bgcolor=ft.Colors.BLACK),
            ft.Text("输入", size=10),
            ft.Container(width=15, height=0),
            ft.Container(width=15, height=3, bgcolor=ft.Colors.BLUE),
            ft.Text("期望输出", size=10, color=ft.Colors.BLUE),
            ft.Container(width=15, height=0),
            ft.Container(width=15, height=3, bgcolor=ft.Colors.GREEN),
            ft.Text("实际输出", size=10, color=ft.Colors.GREEN),
        ], spacing=5)
        
        # 返回完整的波形图
        return ft.Container(
            content=ft.Column([
                # 图例
                legend,
                ft.Divider(height=1),
                # 波形图主体
                ft.Row([
                    # 信号标签列 - 使用 Column 确保垂直对齐
                    ft.Column(
                        signal_labels, 
                        spacing=0, 
                        width=110,
                        height=total_height,
                    ),
                    # 波形区域
                    ft.Column([
                        waveform_stack,
                        # 时间刻度
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
        """构建单个信号的波形段"""
        segments = []
        prev_x = 0
        prev_val = None
        
        for i, point in enumerate(data):
            time = point['time']
            val = point.get(value_key, point.get('value', '0'))
            
            # 计算x位置
            x = int((time - min_time) * time_scale)
            
            if i == 0:
                prev_x = x
                prev_val = val
                continue
            
            # 绘制从前一个点到当前点的线段
            width = max(2, x - prev_x)
            
            # 数值转电平 (0=低, 1=高, 2=未知)
            val_num = self._parse_logic_value(prev_val)
            
            # 波形高度位置 (高电平在上，低电平在下)
            if val_num == 1:
                y_offset = y_base  # 高电平
            elif val_num == 0:
                y_offset = y_base + 12  # 低电平
            else:
                y_offset = y_base + 6  # 中间态
            
            # 创建水平波形段
            segment = ft.Container(
                width=width,
                height=2 if val_num != 2 else 6,
                bgcolor=color,
                margin=ft.margin.only(left=prev_x, top=y_offset),
            )
            segments.append(segment)
            
            # 添加垂直跳变线（如果值发生变化）
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
        
        # 添加最后一个点
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
        """解析逻辑值为数字 (0=低, 1=高, 2=未知/其他)"""
        if val in ['0', "1'b0", "1'h0"]:
            return 0
        elif val in ['1', "1'b1", "1'h1"]:
            return 1
        elif val in ['x', 'X', 'z', 'Z', '?']:
            return 2
        else:
            # 尝试解析数字
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
        """从输出中提取所有信号名"""
        signals = []
        for line in output.split('\n'):
            if 'time=' in line or 't=' in line:
                # 匹配 name=value 对
                for match in re.finditer(r'(\w+)=([\w\'b\d]+)', line):
                    sig = match.group(1)
                    if sig not in ['time', 't'] and sig not in signals:
                        signals.append(sig)
        return signals
    
    def _save_test_result(self, exec_result: ExecutionResult):
        """保存测试结果（使用ID命名，按题目子文件夹组织）"""
        result_data = {
            "test_time": datetime.now().isoformat(),
            "question_id": self.question_id,
            "compile_success": exec_result.compile_success,
            "run_success": exec_result.run_success,
            "output": exec_result.output,
            "error": exec_result.error,
            "vcd_file": exec_result.vcd_file,
        }
        
        # 使用ID作为子目录
        question_dir = os.path.join(SUBMISSIONS_DIR, f"week{self.week}", self.question_id)
        os.makedirs(question_dir, exist_ok=True)
        
        result_file = os.path.join(question_dir, "result.json")
        
        try:
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存测试结果失败: {e}")
    
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
                self._show_report_dialog()
    
    def _on_prev_question(self, e):
        """上一题按钮点击"""
        if self.question_index > 0:
            self.app.navigate_to_question(self.question_index - 1)
    
    def _mark_week_completed(self):
        """标记本周已完成（遍历所有题目子文件夹）"""
        week_dir = os.path.join(SUBMISSIONS_DIR, f"week{self.week}")
        
        if not os.path.exists(week_dir):
            return
            
        try:
            # 遍历所有题目子文件夹
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
                        print(f"标记题目 {qid} 完成状态失败: {e}")
        except Exception as e:
            print(f"标记完成状态失败: {e}")
    
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
