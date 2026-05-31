"""
Verilog作业考试系统 - 配置文件
"""
import os
import sys

# Version info
VERSION = "0.1.0"
APP_NAME = "Verilog Quiz System"


def get_app_data_dir():
    """Get application data directory"""
    # Detect if running in a packaged/bundled application.
    # 1. PyInstaller sets sys.frozen = True
    # 2. flet build uses serious_python and does NOT set sys.frozen,
    #    but sets FLET_APP_STORAGE_DATA environment variable
    # 3. sys.argv[0] may be the app binary or the .py script depending on launcher
    is_packaged = False
    if getattr(sys, 'frozen', False):
        is_packaged = True
    elif os.environ.get('FLET_APP_STORAGE_DATA'):
        # flet build sets this env var
        is_packaged = True
    elif sys.argv:
        argv0 = sys.argv[0]
        if argv0 and not argv0.endswith(('.py', '.pyc', '.pyo')):
            is_packaged = True
    
    if is_packaged:
        # Packaged program: use standard OS-specific user data directory
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
            # Linux: follow XDG Base Directory spec
            xdg_data_home = os.environ.get('XDG_DATA_HOME')
            if xdg_data_home:
                base_dir = os.path.join(xdg_data_home, 'verilog-quiz')
            else:
                base_dir = os.path.join(
                    os.path.expanduser('~'),
                    '.local',
                    'share',
                    'verilog-quiz'
                )
    else:
        # Development environment: use a dedicated subdir inside project
        # to avoid mixing data files with source code
        project_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.join(project_dir, '.data')
    
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
