"""
报告生成器 v2 - 产出结构化报告数据（不落盘 Markdown）

渲染为 PDF 由 core/pdf_generator.py 完成。
"""
import json
import os
import re
from datetime import datetime
from typing import Optional

import config
from core.result_analyzer import result_analyzer


class ReportGenerator:
    """整合题目、学生代码、测试结果与数值对比，产出结构化报告数据。"""

    def build_week_report(self, week: int, student: dict = None) -> Optional[dict]:
        """返回结构化报告数据；本周无题目数据时返回 None。"""
        student = student or {}
        draw_data = self._read_json(os.path.join(
            config.QUESTIONS_DIR, f"week{week}", "draw_result.json"))
        if not draw_data:
            return None
        drawn_questions = draw_data.get("drawn_questions", [])

        info = self._read_json(os.path.join(
            config.QUESTIONS_DIR, f"week{week}", "info.json"), {}) or {}

        questions = []
        for idx, q_info in enumerate(drawn_questions, 1):
            questions.append(self._question_data(week, idx, q_info))

        return {
            "week": week,
            "title": info.get("title", f"Week {week}"),
            "student_id": student.get("student_id", ""),
            "name": student.get("name", ""),
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "questions": questions,
        }

    # ---------- 单题数据 ----------

    def _question_data(self, week: int, index: int, q_info: dict) -> dict:
        qid = q_info["id"]
        result = self._load_test_result(week, qid)
        return {
            "index": index,
            "id": qid,
            "title": q_info.get("title", f"Question {index}"),
            "description": self._filter_images(self._load_question_markdown(week, qid)),
            "code": self._load_student_code(week, qid) or None,
            "result": result,
            "comparison": self._comparison_data(result) if result else None,
        }

    def _comparison_data(self, result: dict) -> Optional[dict]:
        """学生 vs 参考输出的逐时刻数值对比（结构化）。"""
        ref_output = result.get("ref_output", "")
        stu_output = result.get("output", "")
        if not result.get("run_success") or not ref_output or not stu_output:
            return None

        ref_entries = result_analyzer._parse_display_output(ref_output)
        if not ref_entries:
            return None
        signals = [k for k in ref_entries[0].keys() if k != "time"]
        if not signals:
            return None

        analysis = result_analyzer.analyze_from_display(ref_output, stu_output, signals)
        if not analysis.success or not analysis.comparisons:
            return None

        rows = []
        for comp in analysis.comparisons:
            rows.append({
                "time": comp.time,
                "ref": " ".join(f"{k}={v}" for k, v in comp.signal_values.items()),
                "student": " ".join(f"{sig}={comp.actual_outputs.get(sig, '?')}" for sig in signals),
                "match": comp.match,
            })
        return {"rows": rows, "all_match": analysis.all_match}

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
