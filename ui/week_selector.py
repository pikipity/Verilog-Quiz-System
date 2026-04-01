"""
周次选择界面
"""
import os
import json
from datetime import datetime
import flet as ft
from config import QUESTIONS_DIR, SUBMISSIONS_DIR, SERVER_URL


class WeekSelector:
    """周次选择组件"""
    
    def __init__(self, app):
        self.app = app
        self.weeks_data = []
    
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
        start_date = week_info.get("start_date", "")
        end_date = week_info.get("end_date", "")
        select_count = week_info.get("select_count", 0)
        
        # 检查该周的进度
        progress = self._get_week_progress(week)
        completed = progress["completed"]
        total = progress["total"]
        
        # 判断状态
        is_completed = completed >= total and total > 0
        is_in_progress = completed > 0 and not is_completed
        
        # 状态颜色和图标
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
            status_text = f"未开始 0/{total}"
            action_text = "开始"
        
        return ft.Card(
            content=ft.Container(
                content=ft.Row(
                    [
                        # 左侧：周次信息
                        ft.Column(
                            [
                                ft.Text(
                                    f"Week {week}: {title}",
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    f"时间: {start_date} ~ {end_date}",
                                    size=14,
                                    color=ft.Colors.GREY_700,
                                ),
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
                            ],
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
        return ft.Container(
            content=ft.Row(
                [
                    ft.ElevatedButton(
                        "检查更新",
                        icon=ft.Icons.REFRESH,
                        on_click=self._on_check_update,
                    ),
                    ft.Text(
                        f"题目服务器: {SERVER_URL}",
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
        
        # 遍历questions目录
        if not os.path.exists(QUESTIONS_DIR):
            return
        
        for item in os.listdir(QUESTIONS_DIR):
            week_dir = os.path.join(QUESTIONS_DIR, item)
            if not os.path.isdir(week_dir):
                continue
            
            # 检查是否是周次目录（如week1, week2）
            if item.startswith("week"):
                info_file = os.path.join(week_dir, "info.json")
                if os.path.exists(info_file):
                    try:
                        with open(info_file, 'r', encoding='utf-8') as f:
                            info = json.load(f)
                            self.weeks_data.append(info)
                    except Exception as e:
                        print(f"读取{info_file}失败: {e}")
        
        # 按周次排序
        self.weeks_data.sort(key=lambda x: x.get("week", 0))
    
    def _get_week_progress(self, week: int) -> dict:
        """获取周次进度"""
        progress_file = os.path.join(SUBMISSIONS_DIR, f"week{week}", "progress.json")
        
        if os.path.exists(progress_file):
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    questions = data.get("questions", [])
                    completed = sum(1 for q in questions if q.get("status") == "completed")
                    return {
                        "completed": completed,
                        "total": len(questions),
                    }
            except Exception:
                pass
        
        # 检查draw_result获取总题数
        draw_file = os.path.join(QUESTIONS_DIR, f"week{week}", "draw_result.json")
        if os.path.exists(draw_file):
            try:
                with open(draw_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {
                        "completed": 0,
                        "total": len(data.get("drawn_questions", [])),
                    }
            except Exception:
                pass
        
        # 默认返回0
        return {"completed": 0, "total": 0}
    
    def _on_week_click(self, week: int):
        """周次点击事件"""
        # 检查是否需要抽题
        draw_file = os.path.join(QUESTIONS_DIR, f"week{week}", "draw_result.json")
        
        if not os.path.exists(draw_file):
            # 需要下载并抽题
            self.app.show_snackbar("请先点击'检查更新'下载题目", ft.Colors.ORANGE)
            return
        
        # 进入答题界面，从第一题开始
        self.app.show_question_view(week, 0)
    
    def _on_check_update(self, e):
        """检查更新按钮点击"""
        from core.question_manager import question_manager
        
        self.app.show_snackbar("正在检查更新...", ft.Colors.BLUE)
        
        # 检查更新
        has_update, weeks = question_manager.check_update()
        
        if not has_update:
            self.app.show_snackbar("已经是最新题目", ft.Colors.GREEN)
            return
        
        # 有更新，显示对话框
        def confirm_download(e):
            dialog.open = False
            self.app.page.update()
            
            # 下载所有需要更新的周次
            success_count = 0
            for week in weeks:
                self.app.show_snackbar(f"正在下载 Week {week}...", ft.Colors.BLUE)
                if question_manager.download_week(week):
                    success_count += 1
            
            if success_count == len(weeks):
                self.app.show_snackbar(f"成功下载 {success_count} 周题目", ft.Colors.GREEN)
                # 刷新界面
                self._load_weeks_data()
                self.app.show_week_selector()
            else:
                self.app.show_snackbar(f"下载完成: {success_count}/{len(weeks)} 周", ft.Colors.ORANGE)
        
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
