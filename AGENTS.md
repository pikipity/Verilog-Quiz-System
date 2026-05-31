<!-- From: /Users/ze/Documents/GitHub/Verilog-Quiz-System/AGENTS.md -->
# Verilog作业考试系统 - 项目方案

## 项目概述

单机版Verilog作业与考试系统，学生通过GUI界面完成编程题目，程序自动加密保护标准答案，调用iverilog进行仿真测试，生成Markdown格式报告供老师人工判卷。

---

## 技术架构

| 组件 | 技术选择 | 说明 |
|------|---------|------|
| **GUI框架** | Flet (Python) | 原生桌面窗口，Material Design风格，支持Markdown渲染 |
| **网络更新** | HTTP静态文件 | 服务器存放明文题目，程序下载时自动加密 |
| **加密方案** | 内置固定密钥 + SHA256派生 + XOR + Base64 | 防无意查看，明文仅存在于内存 |
| **仿真执行** | iverilog + vvp | 学生自行安装，程序跨平台调用 |
| **波形查看** | GTKWave | 跨平台波形分析工具（必须安装） |
| **报告生成** | Markdown | 纯文本格式，便于老师人工判卷 |

---

## 服务器端结构

```
https://your-server.com/verilog-quiz/
├── manifest.json                    # 全局清单
├── week1/
│   ├── info.json                    # 周次配置（新ID格式）
│   ├── q1/                          # 题库folder（实际内容）
│   │   ├── question.md              # 题目描述（含文字、图片）
│   │   ├── testbench.v              # 测试平台（老师编写）
│   │   └── reference.v              # 标准答案
│   ├── q2/
│   └── ...
├── week2/
└── ...
```

### info.json 格式（新ID格式）

```json
{
  "week": 1,
  "title": "组合逻辑电路基础",
  "updated_at": "2026-04-01T10:00:00",
  "questions": [
    {"id": "mux2to1_v1", "folder": "q1", "title": "2选1数据选择器"},
    {"id": "and2_v1", "folder": "q2", "title": "2输入与门"},
    {"id": "halfadder_v1", "folder": "q3", "title": "半加器"}
  ],
  "select_count": 2
}
```

**关键设计**：`id` 与 `folder` 分离。服务器端按 `folder` 组织文件，客户端下载后以 `id` 作为本地目录名。当题目更新时，可更换 `id` 而保持 `folder` 不变，确保学生能获取到更新后的题目。

---

## 客户端目录结构

```
Verilog-Quiz-System/
├── main.py                          # 程序入口
├── config.py                        # 配置（内置密钥、服务器地址）
├── core/                            # 核心逻辑层
│   ├── __init__.py
│   ├── crypto_manager.py            # 加密/解密管理
│   ├── question_manager.py          # 题目下载、抽题、缓存
│   ├── code_executor.py             # iverilog跨平台调用
│   ├── result_analyzer.py           # 数值结果提取与对比
│   ├── report_generator.py          # Markdown报告生成
│   └── storage.py                   # 本地进度管理（未实现，功能分散在UI层）
├── ui/                              # 界面层
│   ├── __init__.py
│   ├── app.py                       # Flet主应用
│   ├── week_selector.py             # 周次选择（进度显示、检查更新）
│   └── question_view.py             # 答题界面（垂直布局）
├── questions/                       # 本地题目缓存
│   └── week1/
│       ├── info.json                # 周次配置
│       ├── draw_result.json         # 抽题结果记录
│       ├── mux2to1_v1/              # 抽中的题（以id为目录名）
│       │   ├── question.md
│       │   ├── testbench.v
│       │   └── reference.v.enc      # 加密存储
│       └── and2_v1/
│           └── ...
├── submissions/                     # 学生代码保存
│   └── week1/
│       ├── progress.json            # 周级别进度汇总
│       ├── mux2to1_v1/
│       │   ├── mux2to1_v1.v         # 学生代码
│       │   ├── progress.json        # 题目级别进度
│       │   ├── result.json          # 测试结果
│       │   └── temp/                # 临时仿真文件
│       └── and2_v1/
│           └── ...
└── reports/
    └── week1_report.md              # 最终报告
```

---

## 核心流程

### 1. 题目更新与抽题流程

```
启动程序 → 检查manifest → 发现Week 1有更新
  ↓
下载info.json → 获取questions列表和select_count
  ↓
检查本地draw_result.json是否存在
  ├─ 存在 → 读取已抽题目（基于id列表）
  └─ 不存在 → 基于机器指纹生成固定随机种子 → 从id列表中抽select_count道并打乱
  ↓
下载抽中的题目（按folder路径下载，本地以id为目录名存储）
  ↓
reference.v → 内存中加密 → 保存为reference.v.enc → 删除内存明文
  ↓
保存draw_result.json → 显示周次列表
```

### 2. 答题流程

```
选择Week 1 → 自动跳转到第一道未完成的题
  ↓
加载question.md显示题目（图片自动转base64内嵌）
  ↓
检查submissions/week1/{qid}/{qid}.v是否存在 → 加载此前代码到编辑器
  ↓
学生编写代码 → 失焦时自动保存
  ↓
点击"运行测试"
  ↓
检测iverilog环境（跨平台策略见下方章节）
  ↓
临时解密reference.v → 内存中获取标准答案
  ↓
分别编译运行学生代码和参考答案 → 生成各自VCD文件
  ↓
显示编译/运行状态 → 提供GTKWave按钮查看波形
  ↓
保存结果到submissions/week1/{qid}/result.json
  ↓
清除内存中的参考答案
  ↓
点击"保存并继续" → 标记完成，加载下一题
```

### 3. 重做机制

```
已完成Week 1 → 列表显示"Completed"
  ↓
点击进入 → 显示题目选择块（带完成状态）
  ↓
选择其他题目或当前题 → 加载已有代码
  ↓
修改代码 → 自动保存（覆盖）
  ↓
重新运行测试 → 更新result.json
```

### 4. 报告生成流程

```
完成所有题目（或点击"生成报告"）
  ↓
读取draw_result.json确定题目顺序和id
  ↓
遍历每道题（按id查找）
  ├─ 读取question.md（过滤图片语法）
  ├─ 读取submissions/weekN/{qid}/{qid}.v（学生代码）
  └─ 读取submissions/weekN/{qid}/result.json（测试结果）
  ↓
整合生成week1_report.md
  ↓
显示预览 + "打开文件位置"按钮
  ↓
学生手动从学校作业系统提交报告文件
```

---

## 关键设计细节

### 加密策略

- **算法**：SHA256(MASTER_KEY)派生32字节密钥 → XOR循环加密 → Base64编码存储
- **密钥**：程序内置固定32字节密钥（硬编码）
- **范围**：仅加密reference.v，question.md和testbench.v明文存储
- **时机**：下载时立即加密，使用时内存解密，明文不落盘

### 抽题随机策略

- **种子**：基于机器硬件信息（MAC地址/CPU/平台）+ 周次编号生成固定种子
- **特性**：同一台电脑同一周次，每次打开抽题结果相同
- **记录**：draw_result.json保存抽题结果，防止重复抽题
- **格式**：draw_result.json含完整题目信息（id, folder, title, original_index）

### 自动保存策略

- **触发**：编辑器失焦时自动保存、运行测试前
- **位置**：submissions/weekN/{qid}/{qid}.v
- **进度**：同时更新题目级别progress.json和周级别progress.json
- **重做**：直接覆盖原文件，不保留历史版本

### 数值提取策略

- **已实现**：result_analyzer.py可解析`$display`输出（格式`time=10 a=1 b=0 y=1`），生成时间-数值对比表
- **当前UI状态**：测试流程中已保存ExecutionResult，但**未调用result_analyzer进行数值对比展示**
- **备选**：VCD文件解析功能已预留但尚未集成到主流程

### 报告内容格式

```markdown
# Verilog Assignment Report - Week 1: 组合逻辑基础

**Generated**: 2026-04-05 14:30:25
**Questions**: 3

---

## Question 1 (ID: mux2to1_v1)
**Title**: 2选1数据选择器

### Question Description
实现一个2选1数据选择器...

### Student Code
```verilog
module mux2to1(
    input a, b, sel,
    output y
);
    assign y = sel ? b : a;
endmodule
```

### Test Results
**Status**: ✅ Test Completed / ❌ Compilation Failed
**Simulation Output**: ...
```

---

## 界面设计

### 主界面 - 周次选择

垂直布局，顶部标题，中间周次卡片列表，底部操作栏。

```
┌─────────────────────────────────────────────┐
│  Verilog Quiz System                        │
│  Select week to start assignment            │
├─────────────────────────────────────────────┤
│  ┌───────────────────────────────────────┐  │
│  │ Week 1: 组合逻辑基础                    │  │
│  │ ● In Progress 1/2  [Continue]          │  │
│  └───────────────────────────────────────┘  │
│  ┌───────────────────────────────────────┐  │
│  │ Week 2: 时序逻辑入门                    │  │
│  │ ○ Not Started 0/2  [Start]             │  │
│  └───────────────────────────────────────┘  │
├─────────────────────────────────────────────┤
│  [Check Update]    [Open Data Directory]    │
│  Server: http://...                         │
└─────────────────────────────────────────────┘
```

### 答题界面

**垂直单列布局**（整个页面可滚动）：

```
┌───────────────────────────────────────────────────────────┐
│ [←]  Week 1 - Question 1/2                    ID: mux2...  │
│       2选1数据选择器                                       │
├───────────────────────────────────────────────────────────┤
│  Question Selection [1. 2选1选择器 ●] [2. 2输入与门 ○]    │
├───────────────────────────────────────────────────────────┤
│  Question Description                                      │
│  ───────────────────────────────                          │
│  ## 2选1数据选择器                                          │
│  实现根据sel选择a或b输出...                                 │
│  [Markdown渲染，含base64图片]                               │
├───────────────────────────────────────────────────────────┤
│  Code Editor                                               │
│  ───────────────────────────────                          │
│  1│  module mux2to1(                                       │
│  2│      input a, b, sel,                                  │
│  3│      output y                                          │
│  4│  );                                                    │
│  5│      // Write your code here                           │
│  6│  endmodule                                             │
├───────────────────────────────────────────────────────────┤
│  Testbench (read-only)                                     │
│  ───────────────────────────────                          │
│  1│  `timescale 1ns/1ps                                   │
│  2│  module tb_mux2to1;                                   │
│  ...                                                       │
├───────────────────────────────────────────────────────────┤
│  Saved 14:30:25    [Previous] [Run Test] [Save & Continue] │
└───────────────────────────────────────────────────────────┘
```

### 测试结果对话框

```
┌─────────────────────────────────────────────────┐
│  Test Results                          [Close]  │
├─────────────────────────────────────────────────┤
│  [✓]  Simulation Successful                      │
│  Your code compiled and ran successfully.       │
│                                                 │
│  [View Expected Waveform]  [View Your Waveform] │
└─────────────────────────────────────────────────┘
```

---

## 跨平台iverilog调用策略

### 平台检测与调用优先级

| 平台 | 调用策略 | 说明 |
|------|---------|------|
| **Linux** | 直接调用 `iverilog` | 系统PATH中需存在 |
| **macOS** | 直接调用 `iverilog` | 系统PATH中需存在 |
| **Windows** | 1. 尝试直接调用 `iverilog`<br>2. 失败则尝试 `wsl iverilog` | 优先原生，次选WSL |

### 路径处理（Windows + WSL）

Windows路径与WSL路径自动转换：
- `C:\Users\name\project` → `/mnt/c/Users/name/project`
- 程序内部自动处理，学生无需手动干预

### 调用流程

```python
def execute_iverilog(command_args, cwd):
    system = platform.system()
    
    if system in ['Linux', 'Darwin']:
        return subprocess.run(['iverilog'] + command_args, cwd=cwd, ...)
    
    elif system == 'Windows':
        try:
            return subprocess.run(['iverilog'] + command_args, cwd=cwd, ...)
        except FileNotFoundError:
            # WSL fallback
            wsl_args = [convert_to_wsl_path(arg) for arg in command_args]
            return subprocess.run(['wsl'] + wsl_args, ...)
```

---

## GTKWave 波形查看策略

GTKWave是本系统的必须外部依赖，用于查看仿真生成的VCD波形文件。

### 跨平台检测与调用

| 平台 | 检测策略 | 调用方式 |
|------|---------|------|
| **Windows** | 1. `C:\Program Files\GTKWave\bin\gtkwave.exe`<br>2. `wsl which gtkwave` | 原生exe 或 `wsl gtkwave` |
| **macOS** | `gtkwave --version` / `open -a GTKWave` | `open -a GTKWave` 或 `gtkwave` |
| **Linux** | `gtkwave --version` | 直接调用 `gtkwave` |

### Tcl脚本自动生成

程序会自动解析VCD文件中的所有信号名，生成Tcl脚本用于GTKWave自动添加所有信号并缩放到合适视图：
```tcl
gtkwave::addSignalsFromList "tb.dut.a"
gtkwave::addSignalsFromList "tb.dut.b"
gtkwave::/Time/Zoom/Zoom_Full
```

### 测试流程中的VCD

运行测试时，程序会自动修改testbench中的`$dumpfile`名称：
- 参考代码测试 → `ref_wave.vcd`
- 学生代码测试 → `student_wave.vcd`

学生可在测试结果对话框中分别打开"期望波形"和"你的波形"进行对比。

---

## 开发阶段

### 第一阶段：基础框架 ✅

- [x] Flet主程序搭建与页面路由
- [x] 周次选择界面（进度状态）
- [x] 代码编辑器组件（TextField + 等宽字体 + 行号显示）

### 第二阶段：题目系统 ✅

- [x] HTTP下载功能（manifest解析、文件下载）
- [x] 加密管理器（内置密钥、下载时加密）
- [x] 抽题算法（机器指纹种子、draw_result持久化）
- [x] 题目管理器（新ID格式、抽题、缓存、读取）
- [x] Markdown图片base64内嵌

### 第三阶段：仿真执行 ✅

- [x] iverilog跨平台检测与调用
- [x] iverilog调用封装（编译+运行）
- [x] 结果解析器（$display提取）
- [x] 分别运行学生代码和参考代码
- [x] 生成独立VCD文件

### 第四阶段：保存与重做 ✅

- [x] 失焦自动保存
- [x] 进度管理（题目级别 + 周级别progress.json）
- [x] 重做机制（题目选择块快速跳转）

### 第五阶段：报告系统 ✅

- [x] 单题结果存储（JSON格式）
- [x] Markdown报告生成器（整合多题、过滤图片）
- [x] "打开文件位置"功能

### 第六阶段：波形查看 ✅

- [x] GTKWave跨平台集成
- [x] Tcl脚本自动生成
- [x] 期望波形 vs 学生波形对比查看

### 待优化

- [ ] 数值对比表格在UI中展示（result_analyzer已实现，但未在question_view中调用）
- [ ] 定时自动保存（当前仅失焦保存）
- [ ] 代码语法高亮

---

## 部署清单

### 服务器端

- [ ] Web服务器（Nginx/Apache/其他）
- [ ] 创建 `/verilog-quiz/` 目录
- [ ] 按周次组织题目文件夹（使用folder名如q1, q2）
- [ ] 每道题包含：question.md、testbench.v、reference.v
- [ ] 提供 manifest.json 和 info.json（新ID格式）
- [ ] 配置CORS支持（客户端跨域访问）

### 客户端

- [ ] Python 3.11+ 环境（开发用）
- [ ] iverilog 自行安装（学生根据系统选择安装方式）
- [ ] GTKWave 自行安装（必须，用于波形查看）
- [ ] PyInstaller 打包配置（仅打包程序，不含iverilog/GTKWave）

---

## 使用流程

### 老师视角

1. **准备题目**：编写 question.md、testbench.v、reference.v
2. **分配ID**：为每道题分配独立id（如`mux2to1_v1`），放入folder（如`q1`）
3. **配置info.json**：填写questions列表、select_count、updated_at时间戳
4. **上传服务器**：按周次文件夹上传到Web服务器
5. **完成**：无需加密操作，无需编写服务器程序

### 学生视角

1. **安装iverilog**：根据系统安装iverilog
2. **安装GTKWave**：根据系统安装GTKWave（必须）
3. **运行程序**：双击 exe 打开
4. **检查更新**：自动或手动检查新题目
5. **选择周次**：查看进度状态，选择当前作业
6. **答题**：逐题编写代码，失焦自动保存，运行测试查看编译/运行状态
7. **查看波形**：点击GTKWave按钮查看期望波形和自己的波形
8. **重做**：可随时返回修改已完成的题目
9. **生成报告**：完成后生成Markdown文件
10. **提交**：手动将报告文件上传到学校作业系统

---

## 本地测试指南

### 测试环境准备

1. **安装iverilog**
   - Windows: http://bleyer.co.uk/icarus/ 或 WSL (`sudo apt-get install iverilog`)
   - Linux: `sudo apt-get install iverilog`
   - macOS: `brew install icarus-verilog`

2. **安装GTKWave**
   - Windows: https://gtkwave.sourceforge.net/
   - Linux: `sudo apt-get install gtkwave`
   - macOS: `brew install gtkwave`

3. **确保uv已安装**（项目使用uv管理Python环境）

### 测试步骤

需要同时运行两个程序：HTTP服务器（提供题目）和主程序（GUI界面）。

#### 步骤1：启动测试服务器

```bash
cd <项目目录>
uv run python setup_test_server.py
```

看到以下输出表示服务器启动成功：
```
🚀 服务器启动: http://localhost:8080
📁 题目地址: http://localhost:8080/verilog-quiz
```

**保持此终端运行，不要关闭！**

#### 步骤2：运行主程序（GUI界面）

```bash
cd <项目目录>
uv run python main.py
```

#### 步骤3：功能测试流程

1. **检查更新**：点击"Check Update"按钮
2. **下载题目**：程序自动抽题并下载
3. **开始答题**：选择周次，程序自动跳转到第一题
4. **运行测试**：编写代码后点击"Run Test"
5. **查看波形**：点击"View Your Waveform"打开GTKWave
6. **保存继续**：完成所有题目后生成报告

### 常见问题

**Q: 提示"无法连接到服务器"**
- A: 检查测试服务器是否还在运行
- A: 检查 `config.py` 中的 `SERVER_URL` 是否为 `http://localhost:8080/verilog-quiz`

**Q: 提示"未检测到iverilog"**
- A: 确保iverilog已安装并添加到系统PATH
- A: Windows用户可以尝试在WSL中安装iverilog

**Q: 提示"GTKWave not found"**
- A: 确保GTKWave已安装（必须组件）
- A: Windows用户：确保安装在 `C:\Program Files\GTKWave\bin\gtkwave.exe`

**Q: 如何重新测试下载流程？**
- A: 删除 `questions/` 目录下的内容（保留.gitkeep），重新点击"Check Update"

---

## 技术约束与注意事项

1. **iverilog依赖**：学生需自行安装iverilog，程序自动检测环境并提示
2. **GTKWave依赖**：学生需自行安装GTKWave，程序自动检测并支持跨平台调用
3. **Windows双模式**：Windows优先尝试原生iverilog/GTKWave，失败自动 fallback 到WSL
4. **WSL路径转换**：Windows使用WSL时自动处理Windows路径与Linux路径转换
5. **网络需求**：首次下载题目需联网，答题过程可离线
6. **加密限制**：内置密钥可被反编译获取，主要防无意查看，不防专业破解
7. **随机一致性**：基于机器硬件信息，更换电脑会导致抽题结果变化
8. **testbench规范**：老师需确保testbench与reference.v端口一致，且包含`$dumpfile`用于生成VCD
9. **数值对比**：result_analyzer模块已实现$display输出解析和对比逻辑，但当前UI测试流程中尚未调用展示
