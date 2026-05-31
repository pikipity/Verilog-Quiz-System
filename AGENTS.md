# Verilog作业考试系统 - 项目方案

## 项目概述

单机版Verilog作业与考试系统，学生通过GUI界面完成编程题目，程序自动加密保护标准答案，生成Markdown格式报告供老师人工判卷。

---

## 技术架构

| 组件 | 技术选择 | 说明 |
|------|---------|------|
| **GUI框架** | Flet (Python) | 原生桌面窗口，Material Design风格，支持Markdown渲染 |
| **网络更新** | HTTP静态文件 | 服务器存放明文题目，程序下载时自动加密 |
| **加密方案** | 内置固定密钥 + XOR + Base64 | 防无意查看，明文仅存在于内存 |
| **仿真执行** | iverilog + vvp | 学生自行安装，程序跨平台调用 |
| **结果对比** | 数值表格 | 解析$display输出或VCD提取时间点数值 |
| **报告生成** | Markdown | 纯文本格式，便于老师人工判卷 |

---

## 服务器端结构

```
https://your-server.com/verilog-quiz/
├── manifest.json                    # 全局清单
├── week1/
│   ├── info.json                    # 周次配置（含抽题数量）
│   ├── q1/ ~ q10/                   # 题库（10道题示例）
│   │   ├── question.md              # 题目描述（含文字、图片）
│   │   ├── testbench.v              # 测试平台（老师编写）
│   │   └── reference.v              # 标准答案
│   └── assets/                      # 图片资源
├── week2/
└── ...
```

### info.json 格式

```json
{
  "week": 1,
  "title": "组合逻辑电路基础",
  "start_date": "2026-04-01",
  "end_date": "2026-04-07",
  "total_questions": 10,
  "select_count": 3,
  "question_pool": ["q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8", "q9", "q10"]
}
```

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
│   ├── code_executor.py             # iverilog调用执行
│   ├── result_analyzer.py           # 数值结果提取与对比
│   ├── report_generator.py          # Markdown报告生成
│   └── storage.py                   # 本地进度管理
├── ui/                              # 界面层
│   ├── __init__.py
│   ├── app.py                       # Flet主应用
│   ├── week_selector.py             # 周次选择（带日期范围）
│   ├── question_view.py             # 答题界面
│   ├── result_view.py               # 数值对比结果展示
│   └── report_viewer.py             # 报告预览
├── questions/                       # 本地题目缓存
│   └── week1/
│       ├── draw_result.json         # 抽题结果记录
│       ├── q3/                      # 抽中的第1题（原q3）
│       │   ├── question.md
│       │   ├── testbench.v
│       │   └── reference.v.enc      # 加密存储
│       ├── q7/                      # 抽中的第2题
│       └── q2/                      # 抽中的第3题
├── submissions/                     # 学生代码保存
│   └── week1/
│       ├── progress.json            # 进度记录
│       ├── q_selected_1.v           # 第1题代码（对应q3）
│       ├── q_selected_1_result.json # 第1题测试结果
│       ├── q_selected_2.v
│       └── q_selected_3.v
└── reports/
    └── week1_report.md              # 最终报告
```

---

## 核心流程

### 1. 题目更新与抽题流程

```
启动程序 → 检查manifest → 发现Week 1有更新
  ↓
下载info.json → 获取total_questions=10, select_count=3
  ↓
检查本地draw_result.json是否存在
  ├─ 存在 → 读取已抽题目（如["q3","q7","q2"]）
  └─ 不存在 → 基于机器指纹生成固定随机种子 → 从10道中抽3道并打乱
  ↓
下载抽中的3道题（q3,q7,q2）的question.md、testbench.v、reference.v
  ↓
reference.v → 内存中加密 → 保存为reference.v.enc → 删除内存明文
  ↓
保存draw_result.json → 显示周次列表（Week 1显示"3道题待完成"）
```

### 2. 答题流程

```
选择Week 1 → 显示第1/3题（实际为q3的内容）
  ↓
加载question.md显示题目
  ↓
检查q_selected_1.v是否存在 → 加载此前代码到编辑器
  ↓
学生编写代码 → 实时自动保存（每30秒/失焦/运行前）
  ↓
点击"运行测试"
  ↓
检测iverilog环境（跨平台策略见下方章节）
  ↓
临时解密reference.v → 内存中获取标准答案
  ↓
分别编译运行学生代码和参考答案 → 生成VCD/捕获输出
  ↓
提取数值对比表（时间点×信号值）
  ↓
显示结果表格（期望 vs 实际 vs 是否匹配）
  ↓
保存结果到q_selected_1_result.json
  ↓
清除内存中的参考答案
  ↓
点击"保存并继续" → 加载第2/3题（实际为q7）
```

### 3. 重做机制

```
已完成Week 1（3/3题）→ 列表显示"已完成，可重做"
  ↓
点击进入 → 显示3道题的完成状态
  ↓
选择"重做第2题" → 加载q_selected_2.v显示此前代码
  ↓
修改代码 → 自动保存（覆盖）
  ↓
重新运行测试 → 更新q_selected_2_result.json
  ↓
提示"报告已过期，请重新生成"
```

### 4. 报告生成流程

```
完成所有题目（或点击"生成报告"）
  ↓
读取draw_result.json确定题目顺序和原题号
  ↓
遍历3道题
  ├─ 读取question.md（过滤图片语法）
  ├─ 读取q_selected_N.v（学生代码）
  └─ 读取q_selected_N_result.json（数值对比）
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

- **算法**：XOR循环加密 + Base64编码存储
- **密钥**：程序内置固定32字节密钥（硬编码）
- **范围**：仅加密reference.v，question.md和testbench.v明文存储
- **时机**：下载时立即加密，使用时内存解密，明文不落盘

### 抽题随机策略

- **种子**：基于机器硬件信息（MAC地址/CPU序列号）+ 周次编号生成固定种子
- **特性**：同一台电脑同一周次，每次打开抽题结果相同
- **记录**：draw_result.json保存抽题结果，防止重复抽题

### 实时保存策略

- **触发**：每30秒自动保存、编辑器失焦、运行测试前、手动Ctrl+S
- **位置**：submissions/weekN/q_selected_M.v
- **重做**：直接覆盖原文件，不保留历史版本

### 数值提取策略

- **优先级**：优先解析`$display`输出（推荐老师在testbench中使用）
- **备选**：若无$display，解析VCD文件提取所有信号变化时间点
- **格式**：统一为时间-数值表格，便于对比

### 报告内容格式

```markdown
# Verilog作业报告 - Week 1: 组合逻辑基础

**生成时间**: 2026-04-05 14:30:25

---

## 题目 1/3 (原题号: q3)

### 题目描述
实现一个2选1数据选择器...（图片已省略）

### 端口定义
| 端口 | 方向 | 位宽 |
|------|------|------|
| a | input | 1 |
| b | input | 1 |
| sel | input | 1 |
| y | output | 1 |

### 学生代码
```verilog
module mux2to1(
    input a, b, sel,
    output y
);
    assign y = sel ? b : a;
endmodule
```

### 测试结果
**状态**: ❌ 未通过

| 时间(ns) | a | b | sel | 期望输出 | 实际输出 | 结果 |
|---------|---|---|-----|---------|---------|------|
| 0 | 0 | 0 | 0 | 0 | 0 | ✓ |
| 10 | 1 | 0 | 0 | 1 | 0 | ✗ |
```

---

## 界面设计

### 主界面 - 周次选择

```
┌─────────────────────────────────────────────┐
│  Verilog作业系统                       [×]  │
├─────────────────────────────────────────────┤
│                                             │
│  可用周次：                                  │
│  ┌───────────────────────────────────────┐  │
│  │ Week 1: 组合逻辑基础                    │  │
│  │ 2026.04.01 - 2026.04.07                │  │
│  │ 进度: 2/3 题  [继续]  [重做]            │  │
│  └───────────────────────────────────────┘  │
│  ┌───────────────────────────────────────┐  │
│  │ Week 2: 时序逻辑入门                    │  │
│  │ 2026.04.08 - 2026.04.14                │  │
│  │ [未开始]                               │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  [检查更新]                                 │
└─────────────────────────────────────────────┘
```

### 答题界面

```
┌───────────────────────────────────────────────────────────┐
│ [← 返回]  Week 1 - 题目 1/3                      [提交]    │
├──────────────────────────┬────────────────────────────────┤
│                          │                                │
│  ## 2选1数据选择器        │  module mux2to1(               │
│                          │      input a, b,               │
│  实现根据sel选择a或b输出...│      input sel,                │
│                          │      output y                  │
│  ### 端口定义             │  );                            │
│  | 端口|方向|位宽|        │      // 在此编写代码            │
│  |--|--|--|              │      assign y = sel ? b : a;   │
│  |a|input|1|             │                                │
│  ...                     │  endmodule                     │
│                          │                                │
│  [题目区 - Markdown]      │  [代码编辑器 - 等宽字体]         │
│                          │                                │
├──────────────────────────┴────────────────────────────────┤
│  状态: 上次保存 14:30:25    [运行测试]  [保存并继续下一题]   │
└───────────────────────────────────────────────────────────┘
```

### 测试结果界面

```
┌───────────────────────────────────────────────────────────┐
│  测试结果                                          [←返回] │
├───────────────────────────────────────────────────────────┤
│  编译状态: ✅ 成功                                         │
│  测试状态: ❌ 未通过                                       │
│                                                           │
│  数值对比：                                                │
│  ┌─────┬───┬───┬─────┬────────┬────────┬──────┐          │
│  │时间  │ a │ b │ sel │ 期望    │ 实际    │ 结果  │          │
│  ├─────┼───┼───┼─────┼────────┼────────┼──────┤          │
│  │ 0   │ 0 │ 0 │ 0   │ 0      │ 0      │ ✓    │          │
│  │ 10  │ 1 │ 0 │ 0   │ 1      │ 0      │ ✗    │          │
│  │ ... │...│...│ ... │ ...    │ ...    │ ...  │          │
│  └─────┴───┴───┴─────┴────────┴────────┴──────┘          │
│                                                           │
│           [返回修改代码]        [保存并继续下一题]          │
└───────────────────────────────────────────────────────────┘
```

---

## 开发阶段

### 第一阶段：基础框架（2天）

- [ ] Flet主程序搭建与页面路由
- [ ] 周次选择界面（日期显示、进度状态）
- [ ] 代码编辑器组件（TextField + 等宽字体 + 简单高亮）

### 第二阶段：题目系统（2天）

- [ ] HTTP下载功能（manifest解析、文件下载）
- [ ] 加密管理器（内置密钥、下载时加密）
- [ ] 抽题算法（机器指纹种子、draw_result持久化）
- [ ] 题目管理器（抽题、缓存、读取）

### 第三阶段：仿真执行（2天）

- [ ] iverilog跨平台检测与调用（Windows优先直接调用，失败则尝试WSL；Linux/Mac直接调用）
- [ ] iverilog调用封装（编译+运行）
- [ ] 结果解析器（$display提取、VCD备选解析）
- [ ] 数值对比逻辑（生成对比表格）

### 第四阶段：保存与重做（1天）

- [ ] 实时自动保存（定时、失焦、运行前）
- [ ] 进度管理（progress.json）
- [ ] 重做机制（加载历史代码）

### 第五阶段：报告系统（2天）

- [ ] 单题结果存储（JSON格式）
- [ ] Markdown报告生成器（整合多题、过滤图片）
- [ ] 报告预览界面
- [ ] "打开文件位置"功能

### 第六阶段：打包与测试（1天）

- [ ] PyInstaller打包为单exe
- [ ] 跨机器抽题一致性测试
- [ ] 加密/解密验证
- [ ] 完整流程测试

---

## 部署清单

### 服务器端

- [ ] Web服务器（Nginx/Apache/其他）
- [ ] 创建 `/verilog-quiz/` 目录
- [ ] 按周次组织题目文件夹
- [ ] 每道题包含：question.md、testbench.v、reference.v
- [ ] 提供 manifest.json 和 info.json

### 客户端

- [ ] Python 3.8+ 环境（开发用）
- [ ] iverilog 自行安装（学生根据系统选择安装方式）
- [ ] PyInstaller 打包配置（仅打包程序，不含iverilog）

---

## 使用流程

### 老师视角

1. **准备题目**：编写 question.md、testbench.v、reference.v
2. **上传服务器**：按周次文件夹上传到Web服务器
3. **配置info.json**：设置周次日期、抽题数量
4. **完成**：无需加密操作，无需编写服务器程序

### 学生视角

1. **安装iverilog**：根据系统安装iverilog（Windows可安装原生版或WSL版；Linux/Mac直接安装）
2. **运行程序**：双击 exe 打开
3. **检查更新**：自动或手动检查新题目
4. **选择周次**：查看日期范围，选择当前作业
5. **答题**：逐题编写代码，实时自动保存，运行测试查看数值对比
6. **重做**：可随时返回修改已完成的题目
7. **生成报告**：完成后生成Markdown文件
8. **提交**：手动将报告文件上传到学校作业系统

---

## 本地测试指南

### 测试环境准备

1. **安装iverilog**
   - Windows: http://bleyer.co.uk/icarus/ 或 WSL (`sudo apt-get install iverilog`)
   - Linux: `sudo apt-get install iverilog`
   - macOS: `brew install icarus-verilog`

2. **确保uv已安装**（项目使用uv管理Python环境）

### 测试步骤

需要同时运行两个程序：HTTP服务器（提供题目）和主程序（GUI界面）。

#### 步骤1：启动测试服务器（提供题目下载）

打开终端1，进入项目目录：

```bash
# 进入项目目录（根据实际路径修改）
cd <项目目录>

# 如果uv在PATH中
uv run python setup_test_server.py

# 如果uv不在PATH中，使用完整路径（根据实际安装位置修改）
<uv完整路径> run python setup_test_server.py
```

看到以下输出表示服务器启动成功：
```
🚀 服务器启动: http://localhost:8080
📁 题目地址: http://localhost:8080/verilog-quiz
```

**保持此终端运行，不要关闭！**

#### 步骤2：运行主程序（GUI界面）

打开终端2（新窗口），进入项目目录：

```bash
# 进入项目目录（根据实际路径修改）
cd <项目目录>

# 如果uv在PATH中
uv run python main.py

# 如果uv不在PATH中，使用完整路径（根据实际安装位置修改）
<uv完整路径> run python main.py
```

#### 步骤3：功能测试流程

1. **检查更新**：点击"检查更新"按钮
   - 正常：弹出"发现新题目"对话框
   - 如果显示"无法连接到服务器"，检查步骤1的服务器是否还在运行

2. **下载题目**：点击"下载"
   - 程序会自动抽题（从题库中随机抽取指定数量）
   - 下载的题目会保存在 `questions/` 目录

3. **开始答题**：选择周次，点击"开始"
   - 左侧显示题目描述
   - 右侧编写Verilog代码

4. **运行测试**：编写代码后点击"运行测试"
   - 程序调用iverilog编译
   - 显示编译结果和数值对比

5. **保存继续**：完成所有题目后生成报告

### 常见问题

**Q: 提示"无法连接到服务器"**
- A: 检查步骤1的测试服务器是否还在运行
- A: 检查 `config.py` 中的 `SERVER_URL` 是否为 `http://localhost:8080/verilog-quiz`

**Q: 提示"未检测到iverilog"**
- A: 确保iverilog已安装并添加到系统PATH
- A: Windows用户可以尝试在WSL中安装iverilog

**Q: 如何重新测试下载流程？**
- A: 删除 `questions/` 目录下的内容（保留.gitkeep），重新点击"检查更新"

---

## 跨平台iverilog调用策略

### 平台检测与调用优先级

| 平台 | 调用策略 | 说明 |
|------|---------|------|
| **Linux** | 直接调用 `iverilog` | 系统PATH中需存在 |
| **macOS** | 直接调用 `iverilog` | 系统PATH中需存在 |
| **Windows** | 1. 尝试直接调用 `iverilog`<br>2. 失败则尝试 `wsl iverilog` | 优先原生，次选WSL |

### 调用流程

```python
def execute_iverilog(command_args, cwd):
    """跨平台执行iverilog"""
    system = platform.system()
    
    if system in ['Linux', 'Darwin']:  # Darwin = macOS
        # Unix系统直接调用
        return subprocess.run(['iverilog'] + command_args, cwd=cwd, ...)
    
    elif system == 'Windows':
        # Windows先尝试直接调用
        try:
            return subprocess.run(['iverilog'] + command_args, cwd=cwd, ...)
        except FileNotFoundError:
            # 直接调用失败，尝试WSL
            try:
                # 注意：路径需要转换为WSL路径格式
                wsl_cwd = convert_to_wsl_path(cwd)
                wsl_args = [convert_to_wsl_path(arg) if is_path(arg) else arg 
                           for arg in command_args]
                return subprocess.run(['wsl', 'iverilog'] + wsl_args, ...)
            except FileNotFoundError:
                raise Exception("未检测到iverilog，请安装iverilog或启用WSL")
```

### 路径处理（Windows + WSL）

Windows路径与WSL路径转换：
- `C:\Users\name\project` → `/mnt/c/Users/name/project`
- 程序需自动处理VCD文件输出路径的双向转换

### 环境检测与提示

程序启动时检测iverilog可用性：
```
检测中...
├─ Windows系统
├─ 尝试直接调用 iverilog... 失败
├─ 尝试 WSL iverilog... 成功
└─ 使用模式: WSL

或

检测中...
├─ Windows系统
├─ 尝试直接调用 iverilog... 失败
├─ 尝试 WSL iverilog... 失败
└─ ❌ 未检测到iverilog
   请按以下步骤安装：
   方案1: 安装原生Windows版 http://bleyer.co.uk/icarus/
   方案2: 在WSL中运行 sudo apt-get install iverilog
```

---

## 技术约束与注意事项

1. **iverilog依赖**：学生需自行安装iverilog，程序自动检测环境并提示
2. **Windows双模式**：Windows优先尝试原生iverilog，失败自动 fallback 到WSL
3. **WSL路径转换**：Windows使用WSL时需自动处理Windows路径与Linux路径转换
4. **网络需求**：首次下载题目需联网，答题过程可离线
5. **加密限制**：内置密钥可被反编译获取，主要防无意查看，不防专业破解
6. **随机一致性**：基于机器硬件信息，更换电脑会导致抽题结果变化
7. **testbench规范**：老师需确保testbench与reference.v端口一致，且包含必要的$display输出
