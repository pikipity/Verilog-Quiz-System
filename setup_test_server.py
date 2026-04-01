"""
快速设置本地测试服务器
"""
import os
import json
import http.server
import socketserver
import threading
import sys


def create_test_data():
    """创建测试题目数据"""
    base_dir = "test_server/verilog-quiz"
    os.makedirs(base_dir, exist_ok=True)
    
    # manifest.json
    manifest = {
        "version": "1.0",
        "weeks": ["week1"]
    }
    with open(f"{base_dir}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    
    # week1/info.json
    week1_dir = f"{base_dir}/week1"
    os.makedirs(week1_dir, exist_ok=True)
    
    info = {
        "week": 1,
        "title": "组合逻辑基础测试",
        "start_date": "2026-04-01",
        "end_date": "2026-04-07",
        "total_questions": 3,
        "select_count": 2,
        "question_pool": ["q1", "q2", "q3"]
    }
    with open(f"{week1_dir}/info.json", "w") as f:
        json.dump(info, f, indent=2)
    
    # 创建3道测试题
    questions = [
        {
            "id": "q1",
            "title": "2选1数据选择器",
            "module": "mux2to1",
            "ports": ["a", "b", "sel", "y"]
        },
        {
            "id": "q2",
            "title": "2输入与门",
            "module": "and2",
            "ports": ["a", "b", "y"]
        },
        {
            "id": "q3",
            "title": "半加器",
            "module": "half_adder",
            "ports": ["a", "b", "sum", "cout"]
        }
    ]
    
    for q in questions:
        q_dir = f"{week1_dir}/{q['id']}"
        os.makedirs(q_dir, exist_ok=True)
        
        # question.md
        md_content = f"""# 题目：{q['title']}

实现一个{q['title']}。

## 端口定义

| 端口 | 方向 | 位宽 | 说明 |
|------|------|------|------|
"""
        for port in q['ports'][:-1]:
            md_content += f"| {port} | input | 1 | 输入 |\n"
        md_content += f"| {q['ports'][-1]} | output | 1 | 输出 |\n"
        
        with open(f"{q_dir}/question.md", "w") as f:
            f.write(md_content)
        
        # reference.v
        if q['id'] == 'q1':
            ref = """module mux2to1(
    input a,
    input b,
    input sel,
    output y
);
    assign y = sel ? b : a;
endmodule
"""
        elif q['id'] == 'q2':
            ref = """module and2(
    input a,
    input b,
    output y
);
    assign y = a & b;
endmodule
"""
        else:
            ref = """module half_adder(
    input a,
    input b,
    output sum,
    output cout
);
    assign sum = a ^ b;
    assign cout = a & b;
endmodule
"""
        
        with open(f"{q_dir}/reference.v", "w") as f:
            f.write(ref)
        
        # testbench.v
        tb = f"""`timescale 1ns/1ps

module tb_{q['module']};
"""
        for port in q['ports'][:-1]:
            tb += f"    reg {port};\n"
        tb += f"    wire {q['ports'][-1]};\n\n"
        
        tb += f"    {q['module']} dut (\n"
        for port in q['ports']:
            tb += f"        .{port}({port}),\n"
        tb = tb.rstrip(",\n") + "\n    );\n\n"
        
        tb += """    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_""" + q['module'] + """);
        
        $display("=== Test Start ===");
        
        // Test case 1
        #0 """
        
        for port in q['ports'][:-1]:
            tb += f"{port}=0; "
        tb = tb.rstrip() + "\n"
        tb += "        #1 $display(\"time=%0t"
        for port in q['ports']:
            tb += f" {port}=%b"
        tb += "\","
        tb += " $time"
        for port in q['ports']:
            tb += f", {port}"
        tb += ");\n\n"
        
        tb += """        // Test case 2
        #10 """
        for i, port in enumerate(q['ports'][:-1]):
            tb += f"{port}={i%2}; "
        tb = tb.rstrip() + "\n"
        tb += "        #1 $display(\"time=%0t"
        for port in q['ports']:
            tb += f" {port}=%b"
        tb += "\","
        tb += " $time"
        for port in q['ports']:
            tb += f", {port}"
        tb += ");\n\n"
        
        tb += """        #10 $display("=== Test End ===");
        $finish;
    end
endmodule
"""
        
        with open(f"{q_dir}/testbench.v", "w") as f:
            f.write(tb)
    
    print(f"✓ 测试数据已创建: {base_dir}")


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """多线程HTTP服务器"""
    allow_reuse_address = True
    daemon_threads = True


def start_server():
    """启动HTTP服务器"""
    os.chdir("test_server")
    
    PORT = 8080
    Handler = http.server.SimpleHTTPRequestHandler
    
    httpd = ThreadedHTTPServer(("", PORT), Handler)
    
    print(f"\n🚀 服务器启动: http://localhost:{PORT}")
    print(f"📁 题目地址: http://localhost:{PORT}/verilog-quiz")
    print("\n按 Ctrl+C 停止服务器\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n停止服务器...")
        httpd.shutdown()
        httpd.server_close()
        print("服务器已停止")


if __name__ == "__main__":
    create_test_data()
    
    print("\n修改 config.py 中的 SERVER_URL 为: http://localhost:8080/verilog-quiz")
    print("\n启动服务器...")
    
    start_server()
