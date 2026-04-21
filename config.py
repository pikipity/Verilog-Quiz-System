"""
Verilog作业考试系统 - 配置文件
"""
import os
import sys

# Version info
VERSION = "0.1.0"
APP_NAME = "Verilog Quiz System"


def get_app_data_dir():
    """Get application data directory (use fixed location after packaging)"""
    # Detect if in PyInstaller packaged environment
    if getattr(sys, 'frozen', False):
        # Packaged program
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
        # Development environment: use current directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    return base_dir


# Base paths
BASE_DIR = get_app_data_dir()

# Local path configuration
QUESTIONS_DIR = os.path.join(BASE_DIR, "questions")
SUBMISSIONS_DIR = os.path.join(BASE_DIR, "submissions")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

# Ensure directories exist
for dir_path in [QUESTIONS_DIR, SUBMISSIONS_DIR, REPORTS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# Server configuration
# Local test server (use after running setup_test_server.py)
# SERVER_URL = "http://localhost:8080/verilog-quiz"

# Production server (modify after deployment)
SERVER_URL = "http://zewang.site/verilog-quiz/Verilog-Quiz-Questions/"

# Encryption configuration (built-in fixed key)
# Note: This is basic protection against accidental viewing, not professional cracking
MASTER_KEY = b"VerilogQuiz2025@SecureKeyForStudents!!"

# Auto-save interval (seconds)
AUTO_SAVE_INTERVAL = 30

# UI configuration
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
CODE_FONT = "Consolas"
CODE_FONT_SIZE = 14
