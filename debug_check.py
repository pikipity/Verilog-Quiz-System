"""
调试检查脚本
"""
import os
import json
from config import QUESTIONS_DIR

print("=== 调试信息 ===\n")

# 1. 检查目录结构
week_dir = os.path.join(QUESTIONS_DIR, "week1")
print(f"1. Week目录: {week_dir}")
print(f"   存在: {os.path.exists(week_dir)}")

# 2. 检查draw_result.json
draw_file = os.path.join(week_dir, "draw_result.json")
print(f"\n2. 抽题结果文件: {draw_file}")
print(f"   存在: {os.path.exists(draw_file)}")

if os.path.exists(draw_file):
    with open(draw_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"   内容: {data}")
    drawn_questions = data.get("drawn_questions", [])
    print(f"   抽中题目: {drawn_questions}")

# 3. 检查每道题的文件
for q_id in ['q1', 'q2', 'q3']:
    q_dir = os.path.join(week_dir, q_id)
    md_file = os.path.join(q_dir, "question.md")
    tb_file = os.path.join(q_dir, "testbench.v")
    ref_file = os.path.join(q_dir, "reference.v.enc")
    
    print(f"\n3. 题目 {q_id}:")
    print(f"   目录存在: {os.path.exists(q_dir)}")
    print(f"   question.md: {os.path.exists(md_file)}")
    print(f"   testbench.v: {os.path.exists(tb_file)}")
    print(f"   reference.v.enc: {os.path.exists(ref_file)}")
    
    if os.path.exists(md_file):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"   question.md大小: {len(content)} 字符")
            print(f"   前50字符: {content[:50]}")
        except Exception as e:
            print(f"   读取错误: {e}")

print("\n=== 检查完成 ===")
