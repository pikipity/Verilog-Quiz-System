"""
报告生成器 - 生成Markdown格式的作业报告
"""
import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from config import QUESTIONS_DIR, SUBMISSIONS_DIR, REPORTS_DIR


class ReportGenerator:
    """
    报告生成器
    
    整合学生代码、测试结果生成Markdown报告
    使用ID系统查找题目和结果
    """
    
    def __init__(self):
        pass
    
    def generate_week_report(self, week: int) -> Optional[str]:
        """
        生成周次报告
        
        Args:
            week: 周次
            
        Returns:
            生成的报告文件路径，失败返回None
        """
        # 读取抽题结果（新格式）
        draw_file = os.path.join(QUESTIONS_DIR, f"week{week}", "draw_result.json")
        if not os.path.exists(draw_file):
            print(f"未找到抽题结果: {draw_file}")
            return None
        
        with open(draw_file, 'r', encoding='utf-8') as f:
            draw_data = json.load(f)
        
        drawn_questions = draw_data.get("drawn_questions", [])
        
        # 读取周次信息
        info_file = os.path.join(QUESTIONS_DIR, f"week{week}", "info.json")
        week_title = f"Week {week}"
        if os.path.exists(info_file):
            with open(info_file, 'r', encoding='utf-8') as f:
                info = json.load(f)
                week_title = info.get("title", week_title)
        
        # 生成报告内容
        report_lines = [
            f"# Verilog作业报告 - Week {week}: {week_title}",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**题目数量**: {len(drawn_questions)}",
            "",
            "---",
            "",
        ]
        
        # 逐题生成（使用ID查找）
        for idx, q_info in enumerate(drawn_questions, 1):
            q_content = self._generate_question_section(week, idx, q_info)
            report_lines.extend(q_content)
            report_lines.extend(["", "---", ""])
        
        # 保存报告
        os.makedirs(REPORTS_DIR, exist_ok=True)
        report_path = os.path.join(REPORTS_DIR, f"week{week}_report.md")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_lines))
        
        print(f"报告已生成: {report_path}")
        return report_path
    
    def _generate_question_section(self, week: int, index: int, q_info: dict) -> List[str]:
        """
        生成单个题目的报告段落
        
        Args:
            week: 周次
            index: 题目序号（从1开始）
            q_info: 题目信息字典（包含id, folder, title）
            
        Returns:
            Markdown行列表
        """
        qid = q_info['id']
        title = q_info.get('title', f'题目{index}')
        
        lines = [f"## 题目 {index} (ID: {qid})",
                 f"**标题**: {title}",
                 ""]
        
        # 1. 题目描述（使用ID目录）
        question_md = self._load_question_markdown(week, qid)
        if question_md:
            question_md = self._filter_images(question_md)
            lines.extend(["### 题目描述", "", question_md])
        
        # 2. 学生代码（使用ID命名）
        code = self._load_student_code(week, qid)
        if code:
            lines.extend(["", "### 学生代码", "", "```verilog", code, "```"])
        else:
            lines.extend(["", "### 学生代码", "", "*未提交代码*"])
        
        # 3. 测试结果（使用ID命名）
        result = self._load_test_result(week, qid)
        if result:
            lines.extend(["", "### 测试结果", ""])
            
            if result.get("success"):
                all_match = result.get("all_match", False)
                status = "✅ 通过" if all_match else "❌ 未通过"
                lines.append(f"**状态**: {status}")
                lines.append("")
                
                # 添加数值对比表格
                comparisons = result.get("comparisons", [])
                if comparisons:
                    lines.append("**数值对比**:")
                    lines.append("")
                    table = self._format_result_table(result)
                    lines.append(table)
            else:
                error = result.get("error_message", "未知错误")
                lines.append(f"**状态**: ❌ 测试失败")
                lines.append(f"**错误**: {error}")
        else:
            lines.extend(["", "### 测试结果", "", "*尚未测试*"])
        
        return lines
    
    def _load_question_markdown(self, week: int, qid: str) -> str:
        """加载题目描述（使用ID作为目录名）"""
        md_file = os.path.join(QUESTIONS_DIR, f"week{week}", qid, "question.md")
        if os.path.exists(md_file):
            with open(md_file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def _filter_images(self, markdown: str) -> str:
        """过滤Markdown中的图片语法"""
        result = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'[图片: \1]', markdown)
        return result
    
    def _load_student_code(self, week: int, qid: str) -> str:
        """加载学生代码（使用ID命名）"""
        code_file = os.path.join(SUBMISSIONS_DIR, f"week{week}", f"{qid}.v")
        if os.path.exists(code_file):
            with open(code_file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def _load_test_result(self, week: int, qid: str) -> Optional[Dict]:
        """加载测试结果（使用ID命名）"""
        result_file = os.path.join(SUBMISSIONS_DIR, f"week{week}", f"{qid}_result.json")
        if os.path.exists(result_file):
            with open(result_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def _format_result_table(self, result: Dict) -> str:
        """格式化结果为Markdown表格"""
        comparisons = result.get("comparisons", [])
        if not comparisons:
            return "无数据"
        
        all_signals = result.get("signals", [])
        
        # 构建表头
        headers = ["时间(ns)"] + all_signals + ["结果"]
        lines = [
            "| " + " | ".join(headers) + " |",
            "|" + "|".join(["------"] * len(headers)) + "|"
        ]
        
        # 数据行
        for comp in comparisons:
            time_val = comp.get("time", 0)
            values = [str(time_val)]
            
            for sig in all_signals:
                val = comp.get("signal_values", {}).get(sig, "-")
                values.append(str(val))
            
            match = comp.get("match", False)
            values.append("✓" if match else "✗")
            
            lines.append("| " + " | ".join(values) + " |")
        
        return "\n".join(lines)


# 单例实例
report_generator = ReportGenerator()
