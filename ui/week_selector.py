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
    """周次选择组件"""
    
    def __init__(self, app):
        self.app = app
        self.weeks_data = []
        self.check_update_btn = None
    
    def build(self) -> ft.Control:
        """构建界面"""
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
        """构建头部"""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Verilog作业系统",
                        size=32,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE,
                    ),
                    ft.Text(
                        "选择周次开始完成作业",
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
        """构建周次列表"""
        if not self.weeks_data:
            return ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.FOLDER_OPEN, size=64, color=ft.Colors.GREY_400),
                        ft.Text("暂无可用题目", size=18, color=ft.Colors.GREY),
                        ft.Text("点击下方按钮检查更新", size=14, color=ft.Colors.GREY_500),
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
        """构建单个周次卡片"""
        week = week_info["week"]
        title = week_info.get("title", f"第{week}周")
        
        # 检查该周的进度
        progress = self._get_week_progress(week)
        completed = progress["completed"]
        total = progress["total"]
        
        # 判断状态
        is_completed = completed >= total and total > 0
        is_in_progress = completed > 0 and not is_completed
        
        # 状态颜色和图标（未开始不显示状态）
        if is_completed:
            status_color = ft.Colors.GREEN
            status_icon = ft.Icons.CHECK_CIRCLE
            status_text = f"已完成 {completed}/{total}"
            action_text = "重做"
        elif is_in_progress:
            status_color = ft.Colors.ORANGE
            status_icon = ft.Icons.PENDING_ACTIONS
            status_text = f"进行中 {completed}/{total}"
            action_text = "继续"
        else:
            status_color = ft.Colors.BLUE
            status_icon = ft.Icons.RADIO_BUTTON_OFF
            status_text = f"未开始 0/{total}"  # 显示未开始状态
            action_text = "开始"
        
        # 构建左侧信息列
        left_column_items = [
            ft.Text(
                f"Week {week}: {title}",
                size=20,
                weight=ft.FontWeight.BOLD,
            ),
        ]
        
        # 只有非未开始状态才显示状态行
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
                        # 左侧：周次信息
                        ft.Column(
                            left_column_items,
                            spacing=8,
                            expand=True,
                        ),
                        # 右侧：操作按钮
                        ft.ElevatedButton(
                            action_text,
                            icon=ft.Icons.PLAY_ARROW if action_text != "重做" else ft.Icons.REFRESH,
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
        """构建底部栏"""
        self.check_update_btn = ft.ElevatedButton(
            "检查更新",
            icon=ft.Icons.REFRESH,
            on_click=self._on_check_update,
        )
        
        # 打开数据目录按钮
        open_data_btn = ft.TextButton(
            "打开数据目录",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=self._on_open_data_directory,
            tooltip=f"数据存储位置: {BASE_DIR}",
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
                        f"服务器: {SERVER_URL}",
                        size=12,
                        color=ft.Colors.GREY,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=20,
        )
    
    def _load_weeks_data(self):
        """加载本地周次数据"""
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
                        print(f"读取{info_file}失败: {e}")
        
        self.weeks_data.sort(key=lambda x: x.get("week", 0))
    
    def _get_week_progress(self, week: int) -> dict:
        """获取周次进度（新格式）"""
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
        """周次点击事件 - 自动跳转到第一个未完成的题目"""
        draw_file = os.path.join(QUESTIONS_DIR, f"week{week}", "draw_result.json")
        
        if not os.path.exists(draw_file):
            self.app.show_snackbar("请先点击'检查更新'下载题目", ft.Colors.ORANGE)
            return
        
        # 读取抽题结果
        try:
            with open(draw_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                drawn_questions = data.get("drawn_questions", [])
        except Exception:
            drawn_questions = []
        
        # 找到第一个未完成的题目索引
        start_index = 0
        for i, q_info in enumerate(drawn_questions):
            qid = q_info.get('id', '')
            if not self._is_question_completed(week, qid):
                start_index = i
                break
        
        self.app.show_question_view(week, start_index)
    
    def _is_question_completed(self, week: int, question_id: str) -> bool:
        """检查指定题目是否已完成"""
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
        """打开数据目录"""
        try:
            if sys.platform == 'win32':
                subprocess.run(['explorer', BASE_DIR])
            elif sys.platform == 'darwin':
                subprocess.run(['open', BASE_DIR])
            else:
                subprocess.run(['xdg-open', BASE_DIR])
            
            self.app.show_snackbar(f"已打开: {BASE_DIR}", ft.Colors.GREEN)
        except Exception as ex:
            self.app.show_snackbar(f"无法打开目录: {ex}", ft.Colors.RED)
    
    def _on_check_update(self, e):
        """检查更新按钮点击"""
        from core.question_manager import question_manager
        import threading
        
        # 创建全屏加载遮罩
        self.loading_overlay = ft.Container(
            content=ft.Column(
                [
                    ft.ProgressRing(width=50, height=50, stroke_width=4),
                    ft.Text("正在连接服务器...", size=16, color=ft.Colors.WHITE),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            ),
            bgcolor=ft.Colors.BLACK54,
            alignment=ft.Alignment.CENTER,
            expand=True,
        )
        
        # 添加到页面最上层
        self.app.page.overlay.append(self.loading_overlay)
        self.app.page.update()
        
        # 在新线程执行检查
        def do_check():
            status, weeks, error_msg = question_manager.check_update()
            
            def update_ui():
                # 移除加载遮罩
                if self.loading_overlay in self.app.page.overlay:
                    self.app.page.overlay.remove(self.loading_overlay)
                
                if status == "error":
                    def close_error(e):
                        error_dialog.open = False
                        self.app.page.update()
                    
                    error_dialog = ft.AlertDialog(
                        title=ft.Text("连接失败", color=ft.Colors.RED),
                        content=ft.Text(error_msg, selectable=True),
                        actions=[ft.ElevatedButton("确定", on_click=close_error)],
                        actions_alignment=ft.MainAxisAlignment.END,
                    )
                    self.app.page.overlay.append(error_dialog)
                    error_dialog.open = True
                
                elif status == "no_update":
                    self.app.show_snackbar("已经是最新题目", ft.Colors.GREEN)
                
                elif status == "success":
                    self._show_download_dialog(weeks)
                
                self.app.page.update()
            
            self.app.page.run_thread(update_ui)
        
        thread = threading.Thread(target=do_check)
        thread.daemon = True
        thread.start()
    
    def _show_download_dialog(self, weeks):
        """显示下载对话框"""
        from core.question_manager import question_manager
        import threading
        
        def confirm_download(e):
            dialog.open = False
            self.app.page.update()
            
            # 创建全屏加载遮罩
            self.loading_overlay = ft.Container(
                content=ft.Column(
                    [
                        ft.ProgressRing(width=50, height=50, stroke_width=4),
                        ft.Text(f"正在下载 {len(weeks)} 周题目...", size=16, color=ft.Colors.WHITE),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                ),
                bgcolor=ft.Colors.BLACK54,
                alignment=ft.Alignment.CENTER,
                expand=True,
            )
            
            # 添加到页面最上层
            self.app.page.overlay.append(self.loading_overlay)
            self.app.page.update()
            
            # 在新线程执行下载
            def do_download():
                success_count = 0
                for i, week in enumerate(weeks):
                    # 更新提示文字
                    def update_text(idx=i):
                        if hasattr(self, 'loading_overlay') and self.loading_overlay:
                            self.loading_overlay.content.controls[1].value = f"正在下载 Week {weeks[idx]}... ({idx+1}/{len(weeks)})"
                            self.app.page.update()
                    
                    self.app.page.run_thread(update_text)
                    
                    if question_manager.download_week(week):
                        success_count += 1
                
                def update_ui():
                    # 移除加载遮罩
                    if hasattr(self, 'loading_overlay') and self.loading_overlay in self.app.page.overlay:
                        self.app.page.overlay.remove(self.loading_overlay)
                    
                    if success_count == len(weeks):
                        self.app.show_snackbar(f"成功下载 {success_count} 周题目", ft.Colors.GREEN)
                        self._load_weeks_data()
                        self.app.show_week_selector()
                    else:
                        self.app.show_snackbar(f"下载完成: {success_count}/{len(weeks)} 周", ft.Colors.ORANGE)
                
                self.app.page.run_thread(update_ui)
            
            thread = threading.Thread(target=do_download)
            thread.daemon = True
            thread.start()
        
        def cancel(e):
            dialog.open = False
            self.app.page.update()
        
        weeks_str = ", ".join([f"Week {w}" for w in weeks])
        
        dialog = ft.AlertDialog(
            title=ft.Text("发现新题目"),
            content=ft.Text(f"发现以下新题目:\n{weeks_str}\n\n是否立即下载？"),
            actions=[
                ft.TextButton("取消", on_click=cancel),
                ft.ElevatedButton("下载", on_click=confirm_download),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.app.page.overlay.append(dialog)
        dialog.open = True
        self.app.page.update()
