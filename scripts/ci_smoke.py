"""
CI 冒烟测试脚本（纯标准库）：对运行中的 v2 实例发 API 请求验证

用法：
  基础冒烟（全平台）：python scripts/ci_smoke.py --port 8899 --token ci-token
  完整 E2E（需 iverilog/yosys + 题目服务器）：
    python scripts/ci_smoke.py --port 8899 --token ci-token --full
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request


def call(base, token, path, method='GET', body=None, expect=200, raw=False):
    req = urllib.request.Request(
        base + path, method=method,
        headers={'X-Quiz-Token': token, 'Content-Type': 'application/json'},
        data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            code, data = r.code, r.read()
    except urllib.error.HTTPError as e:
        code, data = e.code, e.read()
    if code != expect:
        raise AssertionError(f"{method} {path} -> {code}（期望 {expect}）: {data[:300]}")
    return data if raw else json.loads(data)


# week1 测试题目的正确实现（按 qid 映射；新增 week1 题目需同步更新）
CODE_MAP = {
    'mux2to1_v1': 'module mux2to1(input a, input b, input sel, output y);\n'
                  '  assign y = sel ? b : a;\nendmodule\n',
    'and2_v1': 'module and2(input a, input b, output y);\n'
               '  assign y = a & b;\nendmodule\n',
    'halfadder_v1': 'module half_adder(input a, input b, output sum, output cout);\n'
                    '  assign sum = a ^ b;\n  assign cout = a & b;\nendmodule\n',
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--port', type=int, required=True)
    p.add_argument('--token', required=True)
    p.add_argument('--full', action='store_true')
    args = p.parse_args()
    base = f'http://127.0.0.1:{args.port}'

    for _ in range(60):
        try:
            call(base, args.token, '/api/health')
            break
        except Exception:
            time.sleep(1)
    else:
        sys.exit('FAIL: 服务 60s 内未就绪')

    h = call(base, args.token, '/api/health')
    assert h.get('ok') and h.get('version'), f'health 异常: {h}'
    print(f"[PASS] /api/health version={h['version']}")

    call(base, 'wrong-token', '/api/health', expect=401)
    print("[PASS] 无 token 返回 401")

    index = call(base, args.token, '/', raw=True)
    assert b'Weeks' in index and b'Diagnostics' in index
    print("[PASS] 静态页面（英文导航）")

    if not args.full:
        print("== 基础冒烟通过 ==")
        return

    call(base, args.token, '/api/settings', method='PUT',
         body={'student_id': 'ci0001', 'name': 'CI Bot'})
    sync = call(base, args.token, '/api/sync', method='POST')
    assert sync.get('ok'), sync
    print(f"[PASS] 同步: {sync['summary']}")

    questions = call(base, args.token, '/api/weeks/1/questions')['questions']
    assert questions, 'week1 无抽中题目'
    qid = questions[0]['id']
    assert qid in CODE_MAP, f'CI 未覆盖题目 {qid}，请在 scripts/ci_smoke.py 的 CODE_MAP 中补充'

    r = call(base, args.token, f'/api/questions/1/{qid}/test', method='POST',
             body={'code': CODE_MAP[qid]})
    res = r.get('result', {})
    assert r.get('ok') and res.get('run_success') and res.get('ref_run_success'), str(r)[:400]
    print(f"[PASS] 编译+仿真（学生+参考）: {qid}")

    rtl = call(base, args.token, f'/api/questions/1/{qid}/rtl', method='POST', body={})
    assert rtl.get('ok') and 'modules' in rtl.get('netlist', {}), str(rtl)[:400]
    print("[PASS] Yosys RTL 网表生成")

    rep = call(base, args.token, '/api/reports/1/generate', method='POST')
    assert rep.get('ok'), rep
    content = call(base, args.token, '/api/reports/1')['content']
    assert 'ci0001' in content and 'Value Comparison' in content
    print("[PASS] 报告生成（含学号与数值对比表）")

    print("== 完整 E2E 全部通过 ==")


if __name__ == '__main__':
    main()
