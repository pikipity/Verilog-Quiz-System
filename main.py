"""
Verilog作业考试系统 v2 - 启动器

启动本地后端服务，生成随机 token，用默认浏览器打开界面。
打包后为 windowed 模式（无控制台窗口），日志写入数据目录 app.log。

测试钩子：VERILOG_QUIZ_NO_BROWSER=1 时不打开浏览器（CI 无头冒烟用）。
"""
import os
import sys
import webbrowser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from backend.app import create_server, TOKEN


def _log(msg: str):
    """日志只写文件且脱敏：不记录 token、不记录题目服务器地址。"""
    try:
        with open(config.LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(msg + '\n')
    except OSError:
        pass


def main():
    server, port = create_server()
    _log(f"[v{config.VERSION}] 后端已启动: 127.0.0.1:{port}")

    if os.environ.get("VERILOG_QUIZ_NO_BROWSER") != "1":
        webbrowser.open(f"http://127.0.0.1:{port}/?token={TOKEN}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        _log("后端已停止")


if __name__ == '__main__':
    main()
