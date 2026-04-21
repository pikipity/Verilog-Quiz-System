"""
加密所有reference.v文件
"""
import os
from core.crypto_manager import crypto_manager
from config import QUESTIONS_DIR

week_dirs = [d for d in os.listdir(QUESTIONS_DIR) if d.startswith("week")]

for week in week_dirs:
    week_path = os.path.join(QUESTIONS_DIR, week)
    
    for item in os.listdir(week_path):
        q_path = os.path.join(week_path, item)
        if not os.path.isdir(q_path):
            continue
        
        ref_path = os.path.join(q_path, "reference.v")
        if os.path.exists(ref_path):
            enc_path = ref_path + ".enc"
            crypto_manager.encrypt_file(ref_path, enc_path)
            os.remove(ref_path)
            print(f"加密: {week}/{item}/reference.v")

print("\n加密完成!")
