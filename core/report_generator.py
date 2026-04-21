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
    Report Generator
    
    Integrate student code and test results to generate Markdown reports
    Use ID system to find questions and results
    """
    
    def __init__(self):
        pass
    
    def generate_week_report(self, week: int) -> Optional[str]:
        """
        Generate week report
        
        Args:
            week: Week number
            
        Returns:
            Generated report file path, None if failed
        """
        # Read draw result (new format)
        draw_file = os.path.join(QUESTIONS_DIR, f"week{week}", "draw_result.json")
        if not os.path.exists(draw_file):
            print(f"Draw result not found: {draw_file}")
            return None
        
        with open(draw_file, 'r', encoding='utf-8') as f:
            draw_data = json.load(f)
        
        drawn_questions = draw_data.get("drawn_questions", [])
        
        # Read week info
        info_file = os.path.join(QUESTIONS_DIR, f"week{week}", "info.json")
        week_title = f"Week {week}"
        if os.path.exists(info_file):
            with open(info_file, 'r', encoding='utf-8') as f:
                info = json.load(f)
                week_title = info.get("title", week_title)
        
        # Generate report content
        report_lines = [
            f"# Verilog Assignment Report - Week {week}: {week_title}",
            "",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Questions**: {len(drawn_questions)}",
            "",
            "---",
            "",
        ]
        
        # Generate each question (using ID lookup)
        for idx, q_info in enumerate(drawn_questions, 1):
            q_content = self._generate_question_section(week, idx, q_info)
            report_lines.extend(q_content)
            report_lines.extend(["", "---", ""])
        
        # 保存报告
        os.makedirs(REPORTS_DIR, exist_ok=True)
        report_path = os.path.join(REPORTS_DIR, f"week{week}_report.md")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_lines))
        
        print(f"Report generated: {report_path}")
        return report_path
    
    def _generate_question_section(self, week: int, index: int, q_info: dict) -> List[str]:
        """
        Generate report section for single question
        
        Args:
            week: Week number
            index: Question index (starting from 1)
            q_info: Question info dict (contains id, folder, title)
            
        Returns:
            List of Markdown lines
        """
        qid = q_info['id']
        title = q_info.get('title', f'Question {index}')
        
        lines = [f"## Question {index} (ID: {qid})",
                 f"**Title**: {title}",
                 ""]
        
        # 1. Question description (using ID directory)
        question_md = self._load_question_markdown(week, qid)
        if question_md:
            question_md = self._filter_images(question_md)
            lines.extend(["### Question Description", "", question_md])
        
        # 2. Student code (using ID naming)
        code = self._load_student_code(week, qid)
        if code:
            lines.extend(["", "### Student Code", "", "```verilog", code, "```"])
        else:
            lines.extend(["", "### Student Code", "", "*No code submitted*"])
        
        # 3. Test results (using ID naming)
        result = self._load_test_result(week, qid)
        if result:
            lines.extend(["", "### Test Results", ""])
            
            # Check compile and run status
            compile_success = result.get("compile_success", False)
            run_success = result.get("run_success", False)
            
            if not compile_success:
                error = result.get("error", "Compilation failed")
                lines.append(f"**Status**: ❌ Compilation Failed")
                if error:
                    lines.append(f"**Error**: {error}")
            elif not run_success:
                error = result.get("error", "Execution failed")
                lines.append(f"**Status**: ❌ Execution Failed")
                if error:
                    lines.append(f"**Error**: {error}")
            else:
                # Both compile and run successful
                lines.append(f"**Status**: ✅ Test Completed")
                lines.append("")
                
                # Add simulation output (if any)
                output = result.get("output", "")
                if output:
                    lines.append("**Simulation Output**:")
                    lines.append("```")
                    lines.append(output[:500] if len(output) > 500 else output)
                    lines.append("```")
        else:
            lines.extend(["", "### Test Results", "", "*Not tested yet*"])
        
        return lines
    
    def _load_question_markdown(self, week: int, qid: str) -> str:
        """Load question description (using ID as directory name)"""
        md_file = os.path.join(QUESTIONS_DIR, f"week{week}", qid, "question.md")
        if os.path.exists(md_file):
            with open(md_file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def _filter_images(self, markdown: str) -> str:
        """Filter image syntax from Markdown"""
        result = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'[Image: \1]', markdown)
        return result
    
    def _load_student_code(self, week: int, qid: str) -> str:
        """Load student code (using ID naming, organized by question subfolder)"""
        code_file = os.path.join(SUBMISSIONS_DIR, f"week{week}", qid, f"{qid}.v")
        if os.path.exists(code_file):
            with open(code_file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def _load_test_result(self, week: int, qid: str) -> Optional[Dict]:
        """Load test results (using ID naming, organized by question subfolder)"""
        result_file = os.path.join(SUBMISSIONS_DIR, f"week{week}", qid, "result.json")
        if os.path.exists(result_file):
            with open(result_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def _format_result_table(self, result: Dict) -> str:
        """Format result as Markdown table"""
        comparisons = result.get("comparisons", [])
        if not comparisons:
            return "No data"
        
        all_signals = result.get("signals", [])
        
        # Build table headers
        headers = ["Time(ns)"] + all_signals + ["Result"]
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
