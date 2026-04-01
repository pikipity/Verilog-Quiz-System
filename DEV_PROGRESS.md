# Verilog作业考试系统 - 开发进度

## 已完成内容

### 1. 项目结构搭建
```
Verilog-Quiz-System/
├── .venv/                  # uv虚拟环境
├── core/                   # 核心逻辑层
│   ├── __init__.py
│   ├── crypto_manager.py   # 加密/解密管理
│   ├── code_executor.py    # iverilog跨平台调用
│   ├── question_manager.py # 题目下载、抽题
│   ├── result_analyzer.py  # 结果解析与对比
│   └── report_generator.py # Markdown报告生成
├── ui/                     # 界面层
│   ├── __init__.py
│   ├── app.py              # Flet主应用
│   ├── week_selector.py    # 周次选择界面
│   └── question_view.py    # 答题界面
├── questions/              # 题目缓存
├── submissions/            # 学生代码
├── reports/                # 生成报告
├── config.py               # 配置
├── main.py                 # 程序入口
└── pyproject.toml          # uv项目配置
```

### 2. 核心功能实现

| 模块 | 功能 | 状态 |
|------|------|------|
| CryptoManager | XOR+Base64加密，内置密钥 | ✅ |
| CodeExecutor | Windows/Linux/Mac跨平台iverilog调用，支持WSL fallback | ✅ |
| QuestionManager | HTTP下载、机器指纹抽题、加密存储 | ✅ |
| ResultAnalyzer | $display输出解析、数值对比 | ✅ |
| ReportGenerator | Markdown报告生成 | ✅ |

### 3. 界面功能

| 界面 | 功能 | 状态 |
|------|------|------|
| WeekSelector | 周次列表、进度显示、检查更新 | ✅ |
| QuestionView | 左右分栏、Markdown显示、代码编辑、测试按钮 | ✅ |

### 4. 已实现流程

1. **抽题流程**：基于机器指纹生成确定性随机序列
2. **加密存储**：下载时加密参考答案，使用时内存解密
3. **代码保存**：自动保存到submissions目录
4. **测试流程**：编译+运行，捕获输出
5. **报告生成**：整合所有题目生成Markdown报告

## 待实现/优化内容

### 高优先级
1. **实际测试执行**：目前测试逻辑有简化，需要完整实现学生代码和参考代码的分别执行和对比
2. **VCD解析**：当没有$display输出时，需要解析VCD文件提取数值
3. **结果界面**：目前只显示状态文字，需要显示数值对比表格
4. **实时保存**：目前只在点击按钮时保存，需要实现定时自动保存

### 中优先级
5. **代码编辑器增强**：语法高亮、行号显示
6. **图片显示**：题目中的图片显示
7. **进度显示优化**：显示准确的完成进度
8. **错误处理**：网络错误、iverilog未安装等友好提示

### 低优先级
9. **配置界面**：允许学生修改服务器地址
10. **导入/导出**：支持题目导入导出
11. **主题切换**：深色模式

## 如何运行

```bash
# 使用uv运行
C:\Users\wangz\.local\bin\uv.exe run python main.py

# 或激活虚拟环境后运行
.venv\Scripts\python.exe main.py
```

## 依赖项

- flet >= 0.83.1 (GUI框架)
- requests >= 2.33.1 (HTTP请求)
- cryptography >= 46.0.6 (加密)
- pyinstaller >= 6.19.0 (打包)

## 外部依赖

- iverilog (学生自行安装)
  - Windows: http://bleyer.co.uk/icarus/ 或 WSL
  - Linux: `sudo apt-get install iverilog`
  - macOS: `brew install icarus-verilog`

## 下一步建议

1. 创建测试服务器和题目数据
2. 完整测试下载→答题→测试→报告的全流程
3. 完善结果展示界面（数值对比表格）
4. 测试跨平台iverilog调用（Windows原生/WSL/Linux/Mac）
