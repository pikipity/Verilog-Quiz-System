"""
Verilog作业考试系统 v2 - 配置

约束（AGENTS.md）：
- 服务器地址不得以明文出现在源码/日志/API/界面中
- 后端零第三方依赖，仅标准库
"""
import base64
import os
import sys

VERSION = "2.0.0"
APP_NAME = "Verilog Quiz System"


def get_app_data_dir() -> str:
    """数据目录：打包后使用平台固定位置，开发时用项目目录"""
    is_packaged = getattr(sys, 'frozen', False)

    if is_packaged:
        if sys.platform == 'win32':
            base_dir = os.path.join(os.environ['LOCALAPPDATA'], 'Verilog-Quiz')
        elif sys.platform == 'darwin':
            base_dir = os.path.join(
                os.path.expanduser('~'),
                'Library', 'Application Support', 'Verilog-Quiz'
            )
        else:
            base_dir = os.path.join(
                os.path.expanduser('~'),
                '.local', 'share', 'verilog-quiz'
            )
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    return base_dir


BASE_DIR = get_app_data_dir()

QUESTIONS_DIR = os.path.join(BASE_DIR, "questions")
SUBMISSIONS_DIR = os.path.join(BASE_DIR, "submissions")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
LOG_FILE = os.path.join(BASE_DIR, "app.log")

for _dir in (QUESTIONS_DIR, SUBMISSIONS_DIR, REPORTS_DIR):
    os.makedirs(_dir, exist_ok=True)


# 服务器地址：拆段 + Base64 编码，运行时拼装，源码中不出现明文
# 开发/测试可用环境变量 VERILOG_QUIZ_SERVER_URL 覆盖（如指向本地测试服务器）
_URL_SEGMENTS = (
    "aHR0cDovL3pld2FuZy5zaXRlL3Zlcmlsb2ctcXVpei8=",
    "VmVyaWxvZy1RdWl6LVF1ZXN0aW9ucy8=",
)


def get_server_url() -> str:
    override = os.environ.get("VERILOG_QUIZ_SERVER_URL")
    if override:
        return override.rstrip('/')
    return "".join(base64.b64decode(s).decode('utf-8') for s in _URL_SEGMENTS).rstrip('/')


# 加密配置（内置固定密钥，防无意查看，不防专业破解）
MASTER_KEY = b"VerilogQuiz2025@SecureKeyForStudents!!"

# 工具锁定版本（诊断页比对用，发布前实测更新）
PINNED_VERSIONS = {
    "iverilog": "12.0",
    "gtkwave": "3.3",
    "yosys": "0.40",
}

# 定时自动保存间隔（秒）
AUTO_SAVE_INTERVAL = 30
