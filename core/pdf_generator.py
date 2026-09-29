"""
PDF 报告渲染器 - fpdf2 + 内嵌 Noto Sans CJK SC

设计要点：
- 报告内容是程序自产的结构化数据，不经过通用 Markdown 解析；
- 题目描述（question.md）走一个受限的 Markdown 子集渲染（标题/段落/表格/代码块/列表/粗体）；
- 字体随包分发（OFL 许可），fpdf2 输出时自动子集化嵌入；
- ✓ 有字形，✗ 无字形 → 用 "X" 代替。
"""
import os
import sys

from fpdf import FPDF
from fpdf.fonts import FontFace

# GitHub 风格配色
_CLR_TEXT = (31, 35, 40)
_CLR_MUTED = (101, 109, 118)
_CLR_BORDER = (209, 213, 219)
_CLR_CODE_BG = (246, 248, 250)
_CLR_BAD = (207, 34, 46)
_CLR_GOOD = (26, 127, 55)

_BASE_SIZE = 9.5
_LINE_H = 5.2


def _font_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'assets', 'fonts')
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'assets', 'fonts')


def _usable(mark: str) -> str:
    """✗ 在 Noto Sans CJK SC 中无字形，替换为 X。"""
    return "X" if mark == "✗" else mark


class _ReportPDF(FPDF):
    def footer(self):
        self.set_y(-12)
        self.set_font("noto", "", 8)
        self.set_text_color(*_CLR_MUTED)
        self.cell(0, 8, f"Page {self.page_no()}/{{nb}}", align="C")


def _new_pdf() -> _ReportPDF:
    pdf = _ReportPDF(format="A4")
    pdf.set_auto_page_break(True, margin=18)
    pdf.set_margins(15, 15, 15)
    font_dir = _font_dir()
    pdf.add_font("noto", "", os.path.join(font_dir, "NotoSansCJKsc-Regular.otf"))
    pdf.add_font("noto", "B", os.path.join(font_dir, "NotoSansCJKsc-Bold.otf"))
    return pdf


def _h(pdf, level: int, text: str):
    sizes = {1: 16, 2: 12.5, 3: 10.5}
    pdf.ln(2 if level > 1 else 0)
    pdf.set_font("noto", "B", sizes.get(level, 10.5))
    pdf.set_text_color(*_CLR_TEXT)
    pdf.multi_cell(0, _LINE_H + 2, text, markdown=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)


def _para(pdf, text: str, size: float = _BASE_SIZE, color=_CLR_TEXT, bold=False):
    pdf.set_font("noto", "B" if bold else "", size)
    pdf.set_text_color(*color)
    pdf.multi_cell(0, _LINE_H, text, markdown=True, new_x="LMARGIN", new_y="NEXT")


def _code_block(pdf, code: str):
    pdf.set_font("noto", "", 8.5)
    pdf.set_fill_color(*_CLR_CODE_BG)
    pdf.set_text_color(*_CLR_TEXT)
    pdf.ln(1)
    pdf.multi_cell(0, 4.6, code, fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)


def _table(pdf, rows):
    pdf.set_font("noto", "", 8.5)
    pdf.ln(1)
    with pdf.table(width=pdf.epw, text_align="LEFT", line_height=5,
                   headings_style=FontFace(emphasis="BOLD", fill_color=_CLR_CODE_BG)) as table:
        for row in rows:
            r = table.row()
            for cell in row:
                r.cell(str(cell))
    pdf.ln(1)


def _divider(pdf):
    pdf.ln(2)
    pdf.set_draw_color(*_CLR_BORDER)
    y = pdf.get_y()
    pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
    pdf.ln(3)


def _render_description(pdf, md_text: str):
    """受限 Markdown 子集渲染：标题/段落/表格/代码块/列表。"""
    lines = md_text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        # 代码块
        if line.strip().startswith("```"):
            buf = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            _code_block(pdf, "\n".join(buf))
            continue

        # 表格
        if line.strip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(set(c) <= set("-: ") for c in cells):  # 跳过分隔行
                    rows.append(cells)
                i += 1
            if rows:
                _table(pdf, rows)
            continue

        # 标题
        stripped = line.strip()
        if stripped.startswith("### "):
            _h(pdf, 3, stripped[4:])
        elif stripped.startswith("## "):
            _h(pdf, 2, stripped[3:])
        elif stripped.startswith("# "):
            _h(pdf, 2, stripped[2:])
        elif stripped.startswith(("- ", "* ")):
            _para(pdf, "• " + stripped[2:])
        elif stripped:
            _para(pdf, stripped)
        i += 1


def build_week_pdf(report: dict, out_path: str):
    """report 为 build_week_report() 的结构化产物。"""
    pdf = _new_pdf()
    pdf.set_title(f"Verilog Assignment Report - Week {report['week']}")
    pdf.set_author(f"{report.get('student_id', '')} {report.get('name', '')}".strip())
    pdf.add_page()

    # 头部
    _h(pdf, 1, f"Verilog Assignment Report - Week {report['week']}: {report['title']}")
    pdf.set_font("noto", "", 9)
    pdf.set_text_color(*_CLR_MUTED)
    pdf.multi_cell(
        0, _LINE_H,
        f"**Student ID**: {report.get('student_id', '')}    "
        f"**Name**: {report.get('name', '')}    "
        f"**Generated**: {report.get('generated', '')}    "
        f"**Questions**: {len(report['questions'])}",
        markdown=True, new_x="LMARGIN", new_y="NEXT")
    _divider(pdf)

    for q in report["questions"]:
        _h(pdf, 2, f"Question {q['index']} (ID: {q['id']})")
        _para(pdf, f"**Title**: {q['title']}")

        if q.get("description"):
            _h(pdf, 3, "Question Description")
            _render_description(pdf, q["description"])

        _h(pdf, 3, "Student Code")
        if q.get("code"):
            _code_block(pdf, q["code"])
        else:
            _para(pdf, "No code submitted", color=_CLR_MUTED)

        _h(pdf, 3, "Test Results")
        result = q.get("result")
        if not result:
            _para(pdf, "Not tested yet", color=_CLR_MUTED)
        elif not result.get("compile_success"):
            _para(pdf, "Status: X Compilation failed", color=_CLR_BAD, bold=True)
            if result.get("error"):
                _code_block(pdf, result["error"])
        elif not result.get("run_success"):
            _para(pdf, "Status: X Simulation failed", color=_CLR_BAD, bold=True)
            if result.get("error"):
                _code_block(pdf, result["error"])
        else:
            _para(pdf, "Status: ✓ Test completed", color=_CLR_GOOD, bold=True)
            output = result.get("output", "")
            if output:
                _code_block(pdf, output[:500] if len(output) > 500 else output)

        comp = q.get("comparison")
        if comp and comp.get("rows"):
            _para(pdf, "Value Comparison (reference vs student):", bold=True)
            rows = [("Time (ns)", "Reference", "Student", "Result")]
            for row in comp["rows"]:
                rows.append((row["time"], row["ref"], row["student"],
                             "✓" if row["match"] else "X"))
            _table(pdf, rows)
            if comp["all_match"]:
                _para(pdf, "Overall: ✓ All values match", color=_CLR_GOOD, bold=True)
            else:
                _para(pdf, "Overall: X Mismatches found", color=_CLR_BAD, bold=True)

        _divider(pdf)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    pdf.output(out_path)
