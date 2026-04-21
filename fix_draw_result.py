"""
修复draw_result.json的编码问题
"""
import os
import json
from config import QUESTIONS_DIR

# 创建正确的draw_result.json
draw_data = {
    "week": 1,
    "drawn_questions": ["q1", "q2", "q3"],
    "draw_time": "2026-04-01T10:00:00"
}

draw_file = os.path.join(QUESTIONS_DIR, "week1", "draw_result.json")

# 使用无BOM的UTF-8写入
with open(draw_file, 'w', encoding='utf-8') as f:
    json.dump(draw_data, f, ensure_ascii=False, indent=2)

print(f"已修复: {draw_file}")

# 验证
with open(draw_file, 'r', encoding='utf-8') as f:
    data = json.load(f)
print(f"验证成功: {data}")
