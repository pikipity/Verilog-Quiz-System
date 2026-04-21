"""
直接设置本地测试数据（不通过HTTP下载）- 使用新ID格式
"""
import os
import json
import shutil
from core.crypto_manager import crypto_manager
from config import QUESTIONS_DIR


def setup_local_data():
    """从test_server复制数据并加密（使用新ID格式）"""
    source_dir = "test_server/verilog-quiz"
    
    if not os.path.exists(source_dir):
        print("错误: test_server目录不存在，请先运行 setup_test_server.py 创建测试数据")
        return False
    
    # 复制整个目录
    for item in os.listdir(source_dir):
        src = os.path.join(source_dir, item)
        dst = os.path.join(QUESTIONS_DIR, item)
        
        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"复制目录: {item}")
    
    # 读取info.json获取ID与folder的映射
    week_dirs = [d for d in os.listdir(QUESTIONS_DIR) if d.startswith("week")]
    
    for week in week_dirs:
        week_path = os.path.join(QUESTIONS_DIR, week)
        info_file = os.path.join(week_path, "info.json")
        
        if not os.path.exists(info_file):
            continue
        
        with open(info_file, 'r', encoding='utf-8') as f:
            info = json.load(f)
        
        # 如果没有时间戳，添加一个
        if 'updated_at' not in info:
            from datetime import datetime
            info['updated_at'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(info, f, ensure_ascii=False, indent=2)
        
        questions = info.get('questions', [])
        select_count = info.get('select_count', 2)
        
        # 模拟抽题（全选，用于本地测试）
        drawn = questions[:select_count] if len(questions) > select_count else questions
        
        # 创建抽题结果（使用新格式）
        draw_result = {
            "week": int(week.replace('week', '')),
            "drawn_questions": [
                {
                    "id": q['id'],
                    "folder": q['folder'],
                    "title": q['title'],
                    "original_index": questions.index(q) + 1
                }
                for q in drawn
            ],
            "draw_time": "2026-04-01T10:00:00"
        }
        
        draw_file = os.path.join(week_path, "draw_result.json")
        with open(draw_file, 'w', encoding='utf-8') as f:
            json.dump(draw_result, f, ensure_ascii=False, indent=2)
        print(f"创建抽题结果: {week}/draw_result.json")
        
        # 重命名文件夹：从folder名改为ID名，并加密reference.v
        for q in questions:
            folder_path = os.path.join(week_path, q['folder'])
            id_path = os.path.join(week_path, q['id'])
            
            if os.path.exists(folder_path):
                # 如果已经是以ID命名的，跳过
                if q['folder'] == q['id']:
                    ref_path = os.path.join(folder_path, "reference.v")
                    if os.path.exists(ref_path):
                        enc_path = ref_path + ".enc"
                        crypto_manager.encrypt_file(ref_path, enc_path)
                        os.remove(ref_path)
                        print(f"加密: {week}/{q['id']}/reference.v")
                    continue
                
                # 重命名文件夹
                if os.path.exists(id_path):
                    shutil.rmtree(id_path)
                shutil.move(folder_path, id_path)
                print(f"重命名: {q['folder']} -> {q['id']}")
                
                # 加密reference.v
                ref_path = os.path.join(id_path, "reference.v")
                if os.path.exists(ref_path):
                    enc_path = ref_path + ".enc"
                    crypto_manager.encrypt_file(ref_path, enc_path)
                    os.remove(ref_path)
                    print(f"加密: {week}/{q['id']}/reference.v")
    
    print("\n本地数据准备完成！")
    print("现在可以直接运行主程序: uv run python main.py")
    return True


if __name__ == "__main__":
    setup_local_data()
