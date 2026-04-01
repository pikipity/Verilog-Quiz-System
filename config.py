"""
Verilog作业考试系统 - 配置文件
"""
import os

# 版本信息
VERSION = "0.1.0"
APP_NAME = "Verilog作业系统"

# 服务器配置
# 本地测试服务器（运行 setup_test_server.py 后使用）
SERVER_URL = "http://localhost:8080/verilog-quiz"

# 生产环境服务器（部署后修改）
# SERVER_URL = "https://your-server.com/verilog-quiz"

# 本地路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_DIR = os.path.join(BASE_DIR, "questions")
SUBMISSIONS_DIR = os.path.join(BASE_DIR, "submissions")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

# 确保目录存在
for dir_path in [QUESTIONS_DIR, SUBMISSIONS_DIR, REPORTS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

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
