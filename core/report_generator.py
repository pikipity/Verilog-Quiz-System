"""
报告生成器 v2 - 学号/姓名头部 + 数值对比表（仅供老师判卷）
"""
import json
import os
import re
from datetime import datetime
from typing import List, Optional

import config
from core.result_analyzer import result_analyzer


class ReportGenerator:
    """整合题目、学生代码、测试结果与数值对比，生成 Markdown 报告。"""

    def generate_week_report(self, week: int, student: dict = None) -> Optional[str]:
        """生成指定周的报告，返回文件路径；失败返回 None。"""
        student = student or {}
        draw_data = self._read_json(os.path.join(
            config.QUESTIONS_DIR, f"week{week}", "draw_result.json"))
        if not draw_data:
            return None
        drawn_questions = draw_data.get("drawn_questions", [])

        info = self._read_json(os.path.join(
            config.QUESTIONS_DIR, f"week{week}", "info.json"), {}) or {}
        week_title = info.get("title", f"Week {week}")

        lines = [
            f"# Verilog Assignment Report - Week {week}: {week_title}",
            "",
            f"**Student ID**: {student.get('student_id', '')}",
            f"**Name**: {student.get('name', '')}",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Questions**: {len(drawn_questions)}",
            "",
            "---",
            "",
        ]

        for idx, q_info in enumerate(drawn_questions, 1):
            lines.extend(self._question_section(week, idx, q_info))
            lines.extend(["", "---", ""])

        os.makedirs(config.REPORTS_DIR, exist_ok=True)
        report_path = os.path.join(config.REPORTS_DIR, f"week{week}_report.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        return report_path

    # ---------- 单题段落 ----------

    def _question_section(self, week: int, index: int, q_info: dict) -> List[str]:
        qid = q_info["id"]
        title = q_info.get("title", f"Question {index}")

        lines = [f"## Question {index} (ID: {qid})", f"**Title**: {title}", ""]

        question_md = self._load_question_markdown(week, qid)
        if question_md:
            lines.extend(["### Question Description", "", self._filter_images(question_md)])

        code = self._load_student_code(week, qid)
        if code:
            lines.extend(["", "### Student Code", "", "```verilog", code, "```"])
        else:
            lines.extend(["", "### Student Code", "", "*No code submitted*"])

        result = self._load_test_result(week, qid)
        lines.extend(["", "### Test Results", ""])
        if result:
            lines.extend(self._test_result_lines(result))
            lines.extend(self._comparison_table(result))
        else:
            lines.append("*Not tested yet*")

        return lines

    def _test_result_lines(self, result: dict) -> List[str]:
        if not result.get("compile_success"):
            lines = ["**Status**: ❌ Compilation Failed"]
            if result.get("error"):
                lines.append(f"**Error**: {result['error']}")
            return lines
        if not result.get("run_success"):
            lines = ["**Status**: ❌ Execution Failed"]
            if result.get("error"):
                lines.append(f"**Error**: {result['error']}")
            return lines

        lines = ["**Status**: ✅ Test Completed", ""]
        output = result.get("output", "")
        if output:
            lines.append("**Simulation Output**:")
            lines.append("```")
            lines.append(output[:500] if len(output) > 500 else output)
            lines.append("```")
        return lines

    def _comparison_table(self, result: dict) -> List[str]:
        """学生 vs 参考输出的逐时刻数值对比表。"""
        ref_output = result.get("ref_output", "")
        stu_output = result.get("output", "")
        if not result.get("run_success") or not ref_output or not stu_output:
            return []

        ref_entries = result_analyzer._parse_display_output(ref_output)
        if not ref_entries:
            return []
        signals = [k for k in ref_entries[0].keys() if k != "time"]
        if not signals:
            return []

        analysis = result_analyzer.analyze_from_display(ref_output, stu_output, signals)
        if not analysis.success or not analysis.comparisons:
            return []

        lines = [
            "",
            "**Value Comparison** (reference vs student):",
            "",
            "| 时间(ns) | 参考 | 学生 | 结果 |",
            "|---|---|---|---|",
        ]
        for comp in analysis.comparisons:
            ref_str = " ".join(f"{k}={v}" for k, v in comp.signal_values.items())
            stu_str = " ".join(f"{sig}={comp.actual_outputs.get(sig, '?')}" for sig in signals)
            mark = "✓" if comp.match else "✗"
            lines.append(f"| {comp.time} | {ref_str} | {stu_str} | {mark} |")

        lines.extend(["", f"**Overall**: {'✅ 全部一致' if analysis.all_match else '❌ 存在不一致'}"])
        return lines

    # ---------- 数据读取 ----------

    def _read_json(self, path: str, default=None):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return default

    def _load_question_markdown(self, week: int, qid: str) -> str:
        md_file = os.path.join(config.QUESTIONS_DIR, f"week{week}", qid, "question.md")
        if os.path.exists(md_file):
            with open(md_file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def _filter_images(self, markdown: str) -> str:
        return re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'[Image: \1]', markdown)

    def _load_student_code(self, week: int, qid: str) -> str:
        code_file = os.path.join(config.SUBMISSIONS_DIR, f"week{week}", qid, f"{qid}.v")
        if os.path.exists(code_file):
            with open(code_file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def _load_test_result(self, week: int, qid: str) -> Optional[dict]:
        return self._read_json(os.path.join(
            config.SUBMISSIONS_DIR, f"week{week}", qid, "result.json"))


report_generator = ReportGenerator()
