"""
修复test_server文件编码
"""
import os

files_content = {
    "test_server/verilog-quiz/manifest.json": '{\n  "version": "1.0",\n  "weeks": ["week1"]\n}',
    
    "test_server/verilog-quiz/week1/info.json": '''{\n  "week": 1,\n  "title": "组合逻辑基础测试",\n  "start_date": "2026-04-01",\n  "end_date": "2026-04-07",\n  "total_questions": 3,\n  "select_count": 2,\n  "question_pool": ["q1", "q2", "q3"]\n}''',

    "test_server/verilog-quiz/week1/q1/question.md": """# 题目：2选1数据选择器

实现一个2选1数据选择器，当sel为0时输出a，为1时输出b。

## 端口定义

| 端口 | 方向 | 位宽 | 说明 |
|------|------|------|------|
| a | input | 1 | 输入a |
| b | input | 1 | 输入b |
| sel | input | 1 | 选择信号 |
| y | output | 1 | 输出 |

## 提示
使用assign语句和条件运算符 ?:
""",

    "test_server/verilog-quiz/week1/q1/reference.v": """module mux2to1(
    input a,
    input b,
    input sel,
    output y
);
    assign y = sel ? b : a;
endmodule
""",

    "test_server/verilog-quiz/week1/q2/question.md": """# 题目：2输入与门

实现一个2输入与门，输出为两个输入的与。

## 端口定义

| 端口 | 方向 | 位宽 | 说明 |
|------|------|------|------|
| a | input | 1 | 输入a |
| b | input | 1 | 输入b |
| y | output | 1 | 输出 |

## 提示
使用assign语句和 & 运算符
""",

    "test_server/verilog-quiz/week1/q2/reference.v": """module and2(
    input a,
    input b,
    output y
);
    assign y = a & b;
endmodule
""",

    "test_server/verilog-quiz/week1/q3/question.md": """# 题目：半加器

实现一个半加器，输入a和b，输出sum（和）和cout（进位）。

## 端口定义

| 端口 | 方向 | 位宽 | 说明 |
|------|------|------|------|
| a | input | 1 | 输入a |
| b | input | 1 | 输入b |
| sum | output | 1 | 和 |
| cout | output | 1 | 进位 |

## 提示
- sum = a ^ b（异或）
- cout = a & b（与）
""",

    "test_server/verilog-quiz/week1/q3/reference.v": """module half_adder(
    input a,
    input b,
    output sum,
    output cout
);
    assign sum = a ^ b;
    assign cout = a & b;
endmodule
""",
}

for filepath, content in files_content.items():
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Fixed: {filepath}")

print("\nAll files fixed!")
