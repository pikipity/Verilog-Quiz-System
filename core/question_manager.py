"""
题目管理器 v2 - 下载、学号抽题、加密存储

仅用标准库（urllib）。同步对账编排见 backend/services/sync_service.py。
"""
import hashlib
import json
import os
import random
import re
import shutil
import urllib.error
import urllib.request
from datetime import datetime

import config
from core.crypto_manager import crypto_manager

HTTP_TIMEOUT = 10


def _request(url: str, timeout: int) -> bytes:
    req = urllib.request.Request(url, headers={'User-Agent': f'VerilogQuiz/{config.VERSION}'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_json(url: str, timeout: int = HTTP_TIMEOUT):
    """下载 JSON；网络错误抛异常，由调用方处理。"""
    return json.loads(_request(url, timeout).decode('utf-8'))


def fetch_text(url: str, timeout: int = HTTP_TIMEOUT):
    """下载文本（404 返回 None），统一换行为 \\n。"""
    try:
        text = _request(url, timeout).decode('utf-8')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    return text.replace('\r\n', '\n').replace('\r', '\n')


def fetch_bytes(url: str, timeout: int = HTTP_TIMEOUT):
    """下载二进制（404 返回 None）。"""
    try:
        return _request(url, timeout)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def read_json(path: str, default=None):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default


def scan_local_weeks() -> set:
    """本地已缓存的周次集合（含 info.json 的 weekN 目录）。"""
    weeks = set()
    if not os.path.isdir(config.QUESTIONS_DIR):
        return weeks
    for name in os.listdir(config.QUESTIONS_DIR):
        m = re.fullmatch(r'week(\d+)', name)
        if m and os.path.isfile(os.path.join(config.QUESTIONS_DIR, name, 'info.json')):
            weeks.add(int(m.group(1)))
    return weeks


def draw_questions(student_id: str, week: int, id_list: list, count: int) -> list:
    """学号种子确定性抽题：同一学号同一周次结果永远相同。"""
    seed_str = f"{student_id}_week{week}"
    seed = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16)
    rng = random.Random(seed)

    if count >= len(id_list):
        drawn = id_list.copy()
    else:
        drawn = rng.sample(id_list, count)
    rng.shuffle(drawn)
    return drawn


def download_week(week: int, info: dict, student_id: str) -> list:
    """
    保存info.json → 学号抽题 → 清理不再抽中的旧题 → 下载抽中题目并加密。
    返回抽中题目信息列表。
    """
    server_url = config.get_server_url()
    week_str = f"week{week}"
    week_dir = os.path.join(config.QUESTIONS_DIR, week_str)
    os.makedirs(week_dir, exist_ok=True)

    with open(os.path.join(week_dir, 'info.json'), 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=2)

    questions = info.get('questions', [])
    select_count = int(info.get('select_count', 0))
    id_list = [q['id'] for q in questions]
    drawn_ids = draw_questions(student_id, week, id_list, select_count)

    drawn_questions = []
    for qid in drawn_ids:
        q_info = next((q for q in questions if q['id'] == qid), None)
        if q_info:
            drawn_questions.append({
                'id': q_info['id'],
                'folder': q_info['folder'],
                'title': q_info.get('title', ''),
                'original_index': questions.index(q_info) + 1,
            })

    # 清理不再抽中的旧题目：题目缓存 + 学生提交一并删除
    old_draw = read_json(os.path.join(week_dir, 'draw_result.json'), {}) or {}
    old_ids = {q.get('id') for q in old_draw.get('drawn_questions', [])}
    for qid in old_ids - set(drawn_ids):
        shutil.rmtree(os.path.join(week_dir, qid), ignore_errors=True)
        shutil.rmtree(os.path.join(config.SUBMISSIONS_DIR, week_str, qid), ignore_errors=True)

    draw_result = {
        'week': week,
        'drawn_questions': drawn_questions,
        'draw_time': datetime.now().isoformat(),
    }
    with open(os.path.join(week_dir, 'draw_result.json'), 'w', encoding='utf-8') as f:
        json.dump(draw_result, f, ensure_ascii=False, indent=2)

    for q in drawn_questions:
        _download_question(server_url, week_str, q, week_dir)

    return drawn_questions


def _download_question(server_url: str, week_str: str, q_info: dict, week_dir: str):
    """下载单题：reference.v 加密存储，question.md/testbench.v 明文，图片落盘。"""
    folder, qid = q_info['folder'], q_info['id']
    base_url = f"{server_url}/{week_str}/{folder}"
    q_dir = os.path.join(week_dir, qid)
    os.makedirs(q_dir, exist_ok=True)

    # reference.v 必须成功：临时明文 → 加密 → 立即删除明文
    ref = fetch_text(f"{base_url}/reference.v")
    if ref is None:
        raise RuntimeError(f"下载 reference.v 失败: {week_str}/{qid}")
    tmp_path = os.path.join(q_dir, 'reference.v.tmp')
    with open(tmp_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(ref)
    crypto_manager.encrypt_file(tmp_path, os.path.join(q_dir, 'reference.v.enc'))
    os.remove(tmp_path)

    for name in ('question.md', 'testbench.v'):
        content = fetch_text(f"{base_url}/{name}")
        if content is not None:
            with open(os.path.join(q_dir, name), 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)

    # 题面中的相对路径图片
    md_path = os.path.join(q_dir, 'question.md')
    if os.path.exists(md_path):
        with open(md_path, 'r', encoding='utf-8') as f:
            md = f.read()
        for _alt, img in re.findall(r'!\[([^\]]*)\]\((?!http://|https://|data:)([^)]+)\)', md):
            data = fetch_bytes(f"{base_url}/{img}")
            if data is not None:
                img_path = os.path.join(q_dir, img)
                os.makedirs(os.path.dirname(img_path), exist_ok=True)
                with open(img_path, 'wb') as f:
                    f.write(data)


def get_reference_code(week: int, question_id: str):
    """临时解密参考答案（仅内存，不落盘）。"""
    enc_path = os.path.join(config.QUESTIONS_DIR, f"week{week}", question_id, "reference.v.enc")
    if not os.path.exists(enc_path):
        return None
    try:
        return crypto_manager.decrypt_file(enc_path)
    except Exception:
        return None


def get_question_info(week: int, question_id: str):
    """从 info.json 中查题目信息。"""
    info = read_json(os.path.join(config.QUESTIONS_DIR, f"week{week}", "info.json"))
    if not info:
        return None
    for q in info.get('questions', []):
        if q['id'] == question_id:
            return q
    return None
