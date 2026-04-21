"""
Verilog作业考试系统 - 配置文件
"""
import os
import sys

# 版本信息
VERSION = "0.1.0"
APP_NAME = "Verilog作业系统"


def get_app_data_dir():
    """获取应用数据目录（打包后使用固定位置）"""
    # 检测是否在 PyInstaller 打包环境
    if getattr(sys, 'frozen', False):
        # 打包后的程序
        if sys.platform == 'win32':
            # Windows: C:\Users\<User>\AppData\Local\Verilog-Quiz
            base_dir = os.path.join(os.environ['LOCALAPPDATA'], 'Verilog-Quiz')
        elif sys.platform == 'darwin':
            # macOS: ~/Library/Application Support/Verilog-Quiz
            base_dir = os.path.join(
                os.path.expanduser('~'), 
                'Library', 
                'Application Support', 
                'Verilog-Quiz'
            )
        else:
            # Linux: ~/.local/share/verilog-quiz
            base_dir = os.path.join(
                os.path.expanduser('~'), 
                '.local', 
                'share', 
                'verilog-quiz'
            )
    else:
        # 开发环境：使用当前目录
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    return base_dir


# 基础路径
BASE_DIR = get_app_data_dir()

# 本地路径配置
QUESTIONS_DIR = os.path.join(BASE_DIR, "questions")
SUBMISSIONS_DIR = os.path.join(BASE_DIR, "submissions")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

# 确保目录存在
for dir_path in [QUESTIONS_DIR, SUBMISSIONS_DIR, REPORTS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# 服务器配置
# 本地测试服务器（运行 setup_test_server.py 后使用）
# SERVER_URL = "http://localhost:8080/verilog-quiz"

# 生产环境服务器（部署后修改）
SERVER_URL = "http://zewang.site/verilog-quiz/Verilog-Quiz-Questions/"

# 加密配置（内置固定密钥）
# 注意：这是基础保护，防止无意查看，不防专业破解
MASTER_KEY = b"VerilogQuiz2025@SecureKeyForStudents!!"

# 自动保存间隔（秒）
AUTO_SAVE_INTERVAL = 30

# 界面配置
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
CODE_FONT = "Consolas"
CODE_FONT_SIZE = 14
