"""
直接设置本地测试数据（不通过HTTP下载）
"""
import os
import shutil
from core.crypto_manager import crypto_manager
from config import QUESTIONS_DIR

def setup_local_data():
    """从test_server复制数据并加密"""
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
    
    # 加密所有reference.v
    week_dirs = [d for d in os.listdir(QUESTIONS_DIR) if d.startswith("week")]
    
    for week in week_dirs:
        week_path = os.path.join(QUESTIONS_DIR, week)
        
        # 查找所有题目目录
        for item in os.listdir(week_path):
            q_path = os.path.join(week_path, item)
            if not os.path.isdir(q_path):
                continue
            
            ref_path = os.path.join(q_path, "reference.v")
            if os.path.exists(ref_path):
                # 加密
                enc_path = ref_path + ".enc"
                crypto_manager.encrypt_file(ref_path, enc_path)
                # 删除明文
                os.remove(ref_path)
                print(f"加密: {week}/{item}/reference.v")
    
    print("\n本地数据准备完成！")
    print("现在可以直接运行主程序: uv run python main.py")
    return True

if __name__ == "__main__":
    setup_local_data()
