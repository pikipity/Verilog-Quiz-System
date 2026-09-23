"""
本地HTTP后端 - 纯标准库实现

安全约束（AGENTS.md）：
- 只绑定 127.0.0.1，端口由系统分配
- /api/* 请求需携带随机 token（X-Quiz-Token 头）
- 校验 Host 头防 DNS rebinding
- 不写任何请求日志（脱敏）

测试钩子（仅开发/CI）：VERILOG_QUIZ_PORT、VERILOG_QUIZ_TOKEN 环境变量
可固定端口与 token，便于无头冒烟测试。
"""
import json
import os
import secrets
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

# 兼容直接运行与 PyInstaller 打包两种形态
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

TOKEN = os.environ.get("VERILOG_QUIZ_TOKEN") or secrets.token_urlsafe(24)

_CONTENT_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.js': 'text/javascript; charset=utf-8',
    '.mjs': 'text/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
}


def get_webui_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'webui')
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'webui')


class QuizHandler(BaseHTTPRequestHandler):
    server_version = "VerilogQuiz/2.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        # 脱敏：不写任何请求日志
        pass

    # ---------- 通用工具 ----------

    def _send_json(self, obj, status: int = 200):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def _host_allowed(self) -> bool:
        host = self.headers.get('Host', '')
        return host.startswith('127.0.0.1') or host.startswith('localhost')

    def _token_ok(self) -> bool:
        return secrets.compare_digest(self.headers.get('X-Quiz-Token', ''), TOKEN)

    def _guard(self) -> bool:
        """Host 校验；API 额外校验 token。通过返回 True。"""
        if not self._host_allowed():
            self._send_json({"error": "forbidden"}, 403)
            return False
        if urlparse(self.path).path.startswith('/api/') and not self._token_ok():
            self._send_json({"error": "unauthorized"}, 401)
            return False
        return True

    # ---------- 路由 ----------

    def do_GET(self):
        if not self._guard():
            return
        path = urlparse(self.path).path
        if path.startswith('/api/'):
            self._handle_api_get(path)
        else:
            self._serve_static(path)

    def do_POST(self):
        if not self._guard():
            return
        path = urlparse(self.path).path
        self._handle_api_post(path)

    def do_PUT(self):
        if not self._guard():
            return
        path = urlparse(self.path).path
        self._handle_api_post(path)

    # ---------- API ----------

    def _handle_api_get(self, path: str):
        if path == '/api/health':
            self._send_json({"ok": True, "version": config.VERSION})
        else:
            self._send_json({"error": "not found"}, 404)

    def _handle_api_post(self, path: str):
        self._send_json({"error": "not found"}, 404)

    # ---------- 静态文件 ----------

    def _serve_static(self, path: str):
        if path in ('/', ''):
            path = '/index.html'

        webui_dir = os.path.abspath(get_webui_dir())
        safe_rel = os.path.normpath(path).lstrip('/\\')
        full_path = os.path.abspath(os.path.join(webui_dir, safe_rel))

        if not full_path.startswith(webui_dir + os.sep) or not os.path.isfile(full_path):
            self.send_error(404)
            return

        ext = os.path.splitext(full_path)[1].lower()
        content_type = _CONTENT_TYPES.get(ext, 'application/octet-stream')

        try:
            with open(full_path, 'rb') as f:
                body = f.read()
        except OSError:
            self.send_error(404)
            return

        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)


def create_server(host: str = '127.0.0.1', port: int = None):
    """创建本地服务。端口默认由系统分配，可用 VERILOG_QUIZ_PORT 固定（测试用）。"""
    if port is None:
        port = int(os.environ.get("VERILOG_QUIZ_PORT", "0"))
    server = ThreadingHTTPServer((host, port), QuizHandler)
    return server, server.server_address[1]
