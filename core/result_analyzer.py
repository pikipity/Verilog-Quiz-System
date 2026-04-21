"""
结果分析器 - 解析仿真结果并生成对比
"""
import os
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ComparisonResult:
    """对比结果"""
    time: int
    signal_values: Dict[str, str]  # 信号名 -> 值
    expected_outputs: Dict[str, str]
    actual_outputs: Dict[str, str]
    match: bool


@dataclass
class AnalysisResult:
    """分析结果"""
    success: bool
    comparisons: List[ComparisonResult]
    all_match: bool
    error_message: str = ""


class ResultAnalyzer:
    """
    结果分析器
    
    解析$display输出或VCD文件，提取数值并对比
    """
    
    def __init__(self):
        pass
    
    def analyze_from_display(
        self, 
        ref_output: str, 
        student_output: str,
        output_signals: List[str]
    ) -> AnalysisResult:
        """
        从$display输出分析结果
        
        期望格式: "time=10 a=1 b=0 sel=0 y=1"
        
        Args:
            ref_output: 参考输出
            student_output: 学生输出
            output_signals: 输出信号名列表
            
        Returns:
            AnalysisResult
        """
        try:
            # 解析两组输出
            ref_values = self._parse_display_output(ref_output)
            student_values = self._parse_display_output(student_output)
            
            if not ref_values:
                return AnalysisResult(
                    success=False,
                    comparisons=[],
                    all_match=False,
                    error_message="无法解析参考输出"
                )
            
            # 对比
            comparisons = []
            all_match = True
            
            for ref_entry in ref_values:
                time = ref_entry.get('time', 0)
                
                # 查找对应时间的学生输出
                student_entry = self._find_entry_by_time(student_values, time)
                
                if student_entry is None:
                    all_match = False
                    comparisons.append(ComparisonResult(
                        time=time,
                        signal_values={k: v for k, v in ref_entry.items() if k != 'time'},
                        expected_outputs={sig: ref_entry.get(sig, '?') for sig in output_signals},
                        actual_outputs={sig: "未找到" for sig in output_signals},
                        match=False
                    ))
                    continue
                
                # 对比输出信号
                expected = {sig: ref_entry.get(sig, '?') for sig in output_signals}
                actual = {sig: student_entry.get(sig, '?') for sig in output_signals}
                match = expected == actual
                
                if not match:
                    all_match = False
                
                comparisons.append(ComparisonResult(
                    time=time,
                    signal_values={k: v for k, v in ref_entry.items() if k != 'time'},
                    expected_outputs=expected,
                    actual_outputs=actual,
                    match=match
                ))
            
            return AnalysisResult(
                success=True,
                comparisons=comparisons,
                all_match=all_match
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                comparisons=[],
                all_match=False,
                error_message=f"分析失败: {e}"
            )
    
    def _parse_display_output(self, output: str) -> List[Dict]:
        """
        解析$display输出
        
        格式: "time=10 a=1 b=0 sel=0 y=1"
        """
        values = []
        
        # 匹配键值对
        for line in output.split('\n'):
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            
            # 查找time=开头的行
            if 'time=' in line:
                entry = {}
                
                # 提取time
                time_match = re.search(r'time=(\d+)', line)
                if time_match:
                    entry['time'] = int(time_match.group(1))
                
                # 提取其他键值对 name=value
                kv_pattern = r'(\w+)=([\w\'b\d]+)'
                for match in re.finditer(kv_pattern, line):
                    key = match.group(1)
                    val = match.group(2)
                    if key != 'time':
                        entry[key] = val
                
                if entry:
                    values.append(entry)
        
        return values
    
    def _find_entry_by_time(self, entries: List[Dict], time: int) -> Optional[Dict]:
        """按时间查找条目"""
        for entry in entries:
            if entry.get('time') == time:
                return entry
        return None
    
    def format_as_table(self, result: AnalysisResult, all_signals: List[str]) -> str:
        """
        格式化为表格字符串（用于显示和报告）
        
        Args:
            result: 分析结果
            all_signals: 所有信号名列表
            
        Returns:
            Markdown表格字符串
        """
        if not result.comparisons:
            return "无测试数据"
        
        # 确定输出信号（对比的信号）
        output_signals = []
        if result.comparisons:
            first = result.comparisons[0]
            output_signals = list(first.expected_outputs.keys())
        
        # 构建表头
        headers = ["时间(ns)"] + all_signals + ["结果"]
        header_line = "| " + " | ".join(headers) + " |"
        separator = "|" + "|".join(["------"] * len(headers)) + "|"
        
        lines = [header_line, separator]
        
        # 构建数据行
        for comp in result.comparisons:
            values = [str(comp.time)]
            
            for sig in all_signals:
                val = comp.signal_values.get(sig, "-")
                values.append(str(val))
            
            status = "✓" if comp.match else "✗"
            values.append(status)
            
            line = "| " + " | ".join(values) + " |"
            lines.append(line)
        
        return "\n".join(lines)
    
    def save_result_json(
        self, 
        result: AnalysisResult, 
        all_signals: List[str],
        output_path: str
    ):
        """
        保存结果为JSON格式
        
        Args:
            result: 分析结果
            all_signals: 所有信号
            output_path: 输出文件路径
        """
        data = {
            "success": result.success,
            "all_match": result.all_match,
            "error_message": result.error_message,
            "signals": all_signals,
            "output_signals": list(result.comparisons[0].expected_outputs.keys()) if result.comparisons else [],
            "comparisons": []
        }
        
        for comp in result.comparisons:
            data["comparisons"].append({
                "time": comp.time,
                "signal_values": comp.signal_values,
                "expected": comp.expected_outputs,
                "actual": comp.actual_outputs,
                "match": comp.match
            })
        
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


# 单例实例
result_analyzer = ResultAnalyzer()
