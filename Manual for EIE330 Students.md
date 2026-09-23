# Verilog 作业考试系统使用手册

# Verilog Quiz System User Manual

---

- [简介 / Introduction](#简介--introduction)
- [支持的平台 / Supported Platforms](#支持的平台--supported-platforms)
- [准备工作 / Prerequisites](#准备工作--prerequisites)
- [下载与运行 / Download and Run](#下载与运行--download-and-run)
- [使用教程 / Usage Tutorial](#使用教程--usage-tutorial)
- [故障排除 / Troubleshooting](#故障排除--troubleshooting)

---

## 简介 / Introduction

本手册面向 EIE330 课程学生，详细介绍如何安装和使用 Verilog 作业考试系统完成课程作业。

This manual is designed for EIE330 course students, providing detailed instructions on how to install and use the Verilog Quiz System to complete course assignments.

v2 版本无需虚拟机，直接在你的电脑上原生运行：双击程序后，系统会自动在浏览器中打开操作界面。

Version 2 runs natively on your own computer (no virtual machine required). Simply double-click the application, and the interface opens automatically in your web browser.

---

## 支持的平台 / Supported Platforms

| 平台 / Platform | 支持状态 / Status | 推荐度 / Recommendation |
|---|---|---|
| Windows 10/11 (x64) | ✅ 完全支持 / Fully supported | ⭐⭐⭐⭐⭐ |
| macOS (Apple Silicon) | ✅ 完全支持 / Fully supported | ⭐⭐⭐⭐ |
| Ubuntu 22.04/24.04 (x64) | ✅ 完全支持 / Fully supported | ⭐⭐⭐⭐ |
| Ubuntu 24.04 (ARM64) | ✅ 完全支持 / Fully supported | ⭐⭐⭐ |

**特别提醒 / Special Note：**

v2 版本起**不再需要使用 VirtualBox 虚拟机**。请直接在你的宿主机系统（Windows / macOS / Linux）上安装运行。

Starting from v2, **VirtualBox is no longer required**. Please install and run the application directly on your host operating system (Windows / macOS / Linux).

---

## 准备工作 / Prerequisites

### 需要预装的软件 / Required Software

在使用本程序之前，你需要安装以下三个软件（请安装指定的版本）：

Before using this application, you need to install the following three software (please install the specified versions):

| 软件 / Software | 用途 / Purpose | 锁定版本 / Required Version |
|---|---|---|
| **Icarus Verilog** | 编译与仿真 / Compile and simulate | **11.0** |
| **GTKWave** | 波形查看器 / Waveform viewer | **3.3.104** |
| **Yosys** | 生成 RTL 电路图 / RTL view generation | **0.9** |

> 以上版本与老师验证环境（Ubuntu 22.04）完全一致，全部功能已在该版本组合上实测通过。
> These versions exactly match the instructor's verified environment (Ubuntu 22.04); all features have been tested against this combination.

### Windows 安装 / Windows Installation

1. **Icarus Verilog v11**（安装包已附带 GTKWave / GTKWave is bundled）
   - 下载 v11 安装包：https://bleyer.org/icarus/iverilog-v11-20210204-x64_setup.exe
   - Download the v11 installer from the link above
   - 安装时**勾选 "Add executable folder(s) to the user PATH"**
   - **Check "Add executable folder(s) to the user PATH"** during installation

2. **GTKWave 3.3.104**
   - 上一步的 iverilog 安装包已附带 GTKWave，通常无需单独安装
   - GTKWave is already bundled with the iverilog installer above, no separate install needed in most cases
   - 如需单独安装：从 <https://gtkwave.sourceforge.net/> 下载 3.3.104 的 Windows 版，解压或安装到 `C:\Program Files\GTKWave\`
   - If you need a separate install: download the 3.3.104 Windows build from the link above
   - 安装到其他位置也可以，之后在程序"设置"页手动指定路径即可
   - Other locations are also fine; you can set the path manually in the app Settings page later

3. **Yosys 0.9**
   - Yosys 0.9 没有官方的 Windows 原生安装包，请二选一 / Yosys 0.9 has no official native Windows package; choose one of the following:
   - **方式一（版本严格一致，推荐）**：安装 WSL2 + Ubuntu 22.04，在 WSL 终端执行 `sudo apt-get install -y yosys`（本程序会自动检测 WSL 中的工具）
     - **Option 1 (exact version match, recommended)**: install WSL2 + Ubuntu 22.04, then run `sudo apt-get install -y yosys` in the WSL terminal (the app detects WSL tools automatically)
   - **方式二（原生 Windows，版本较新）**：下载 OSS CAD Suite <https://github.com/YosysHQ/oss-cad-suite-build/releases>，解压后把 `bin` 目录加入系统 PATH；诊断页会显示 🟡（版本较新），功能已验证可用
     - **Option 2 (native Windows, newer version)**: download OSS CAD Suite, add its `bin` directory to PATH; Diagnostics will show 🟡 (newer version), which is verified to work

### macOS 安装 / macOS Installation

**常规安装（版本较新，诊断页显示 🟡，不影响使用）**：

```bash
brew install icarus-verilog gtkwave yosys
```

- 本程序只使用这些工具的基础功能，新旧版本均兼容，🟡 可以放心使用
- The app only uses basic features of these tools; newer versions with 🟡 are fine

**如需与锁定版本严格一致（iverilog 11.0 / yosys 0.9）**：

Homebrew 不支持直接安装旧版，需要用 `brew extract` 从官方公式历史中提取：

```bash
# 1. 创建本地 tap / Create a local tap
brew tap-new local/versions

# 2. 提取旧版公式并安装 / Extract old formulas and install
brew extract --version 11.0 icarus-verilog local/versions
brew install icarus-verilog@11.0

brew extract --version 0.9 yosys local/versions
brew install yosys@0.9
```

- 注意：提取的旧版没有预编译包，需要现场编译（iverilog 很快；yosys 0.9 在新系统上编译可能遇到问题，遇到时建议直接用常规安装接受 🟡）
- Note: extracted formulas build from source (iverilog is quick; yosys 0.9 may hit build issues on new macOS — if so, just use the regular install and accept 🟡)
- GTKWave 是 GUI 应用（cask），不适用此方法；brew 安装的 3.3.10x 与锁定 3.3.104 同族，🟡 即可
- GTKWave is a GUI app (cask) and this method doesn't apply; the brew-installed 3.3.10x is in the same family as the pinned 3.3.104, 🟡 is fine

### Linux (Ubuntu/Debian) 安装 / Linux Installation

```bash
sudo apt-get update
sudo apt-get install -y iverilog gtkwave yosys
```

- **Ubuntu 22.04**：apt 安装的版本与锁定版本**完全一致**（诊断页全 🟢）
- **Ubuntu 22.04**: apt installs exactly the pinned versions (all 🟢 in Diagnostics)

**Ubuntu 24.04 或其他发行版（版本较新，显示 🟡）**：如需严格对齐，可从 Ubuntu 22.04 (jammy) 的软件包页面手动下载 `.deb` 安装：

For Ubuntu 24.04 or other distros (newer versions, 🟡), to match the pinned versions exactly, download the `.deb` packages from the Ubuntu 22.04 (jammy) package pages:

1. 访问以下页面，下载对应架构（amd64/arm64）的 `.deb` 文件：
   - Visit these pages and download the `.deb` for your architecture:
   - iverilog: https://packages.ubuntu.com/jammy/iverilog
   - gtkwave: https://packages.ubuntu.com/jammy/gtkwave
   - yosys: https://packages.ubuntu.com/jammy/yosys

2. 安装 / Install：

```bash
sudo dpkg -i iverilog_*.deb gtkwave_*.deb yosys_*.deb
sudo apt-get -f install   # 自动补齐依赖 / fix dependencies automatically
```

### 验证安装 / Verify Installation

```bash
# 验证 iverilog / Verify iverilog
iverilog -V
# 预期输出 / Expected: Icarus Verilog version 11.0 (stable)

# 验证 GTKWave / Verify GTKWave
gtkwave --version
# 预期输出 / Expected: GTKWave Analyzer v3.3.104

# 验证 Yosys / Verify Yosys
yosys -V
# 预期输出 / Expected: Yosys 0.9
```

> 安装完成后，也可以直接在程序的"诊断"页面一键检查所有工具，见下文。
> After installation, you can also check all tools in the app's "Diagnostics" page, see below.

---

## 下载与运行 / Download and Run

### 从 GitHub 下载 / Download from GitHub

1. **访问 Releases 页面** / **Visit Releases page**
   - 打开：https://github.com/pikipity/Verilog-Quiz-System/releases
   - 找到最新版本（Latest）

2. **下载对应版本** / **Download for your platform**

   | 你的系统 / Your OS | 下载文件 / Download File |
   |---|---|
   | Windows (x64) | `verilog-quiz-windows.zip` |
   | macOS (Apple Silicon) | `verilog-quiz-macos-arm64.zip` |
   | Linux (x64) | `verilog-quiz-linux.zip` |
   | Linux (ARM64) | `verilog-quiz-linux-arm64.zip` |

3. **解压文件** / **Extract the zip**
   - 解压到任意目录即可，程序免安装
   - Extract to any directory; no installation needed

4. **运行程序** / **Run the application**
   - **Windows**：双击 `verilog-quiz-system.exe`
     - 若出现 SmartScreen 提示，点击"更多信息"→"仍要运行"
     - Double-click `verilog-quiz-system.exe`. If SmartScreen appears, click "More info" → "Run anyway"
   - **macOS**：首次运行对程序图标**右键 → 打开**，在弹窗中再点"打开"
     - First run: **right-click → Open**, then click "Open" in the dialog
   - **Linux**：
     ```bash
     chmod +x verilog-quiz-system
     ./verilog-quiz-system
     ```

5. **浏览器自动打开界面** / **Browser opens automatically**
   - 程序启动后会自动用默认浏览器打开操作界面
   - The interface opens automatically in your default browser
   - 使用期间请不要关闭程序本体 / Do not close the application while using it

---

## 使用教程 / Usage Tutorial

### 首次使用 / First Time Use

1. **填写学号和姓名** / **Enter your student ID and name**
   - 首次启动会进入"设置"页面，**学号必填**
   - First launch opens the Settings page; **student ID is required**
   - 抽题由学号决定：每位同学拿到的题目可能不同，且换电脑后结果不变
   - Question drawing is determined by your student ID: each student may get different questions, and the result stays the same even if you switch computers
   - **注意**：之后修改学号会清空本机全部题目与代码数据（程序会弹出确认框）
   - **Note**: changing your student ID later will erase all local questions and code (a confirmation dialog will appear)

2. **检查工具状态** / **Check tools status**
   - 点击顶部导航的 **"诊断"**，确认 Icarus Verilog、GTKWave、Yosys 均为 🟢
   - Click **"Diagnostics"** in the top navigation and confirm all three tools show 🟢
   - 🟡 表示版本与锁定版本不一致（通常仍可用）；🔴 表示未找到，请回到"准备工作"安装
   - 🟡 means version differs from recommended (usually still works); 🔴 means not found, please go back to Prerequisites
   - 可点击 **"运行自检"** 让程序用内置样例实际验证编译、仿真与 RTL 生成
   - Click **"Run Self-Check"** to verify compilation, simulation, and RTL generation with a built-in sample

3. **下载题目** / **Download questions**
   - 回到"周次"页面，点击 **"检查更新"** 从服务器下载题目
   - Go back to "Weeks" page and click **"Check Update"** to download questions
   - 如果提示连接失败，请检查网络或联系助教
   - If connection fails, check your network or contact the TA

### 答题流程 / Answering Process

1. **题目选择** / **Question Selection**
   - 界面顶部显示所有题目，可快速跳转
   - All questions are displayed at the top for quick navigation
   - 当前题目高亮显示，已尝试的题目（保存过代码）显示 ● 标记
   - Current question is highlighted; attempted questions (code saved) show ●

2. **查看题目** / **View Question**
   - 阅读题目描述，了解功能要求和端口定义
   - Read the question description, understand requirements and port definitions

3. **编写代码** / **Write Code**
   - 在代码编辑器中编写 Verilog 代码（支持语法高亮和行号）
   - Write Verilog code in the editor (with syntax highlighting and line numbers)
   - 代码会**自动保存**（每30秒/失焦时/运行测试前），重启电脑也不会丢失
   - Code **auto-saves** every 30 seconds, on focus out, and before running tests — it survives reboots

4. **查看测试平台** / **View Testbench**
   - 查看 Testbench 代码，了解测试用例和输入信号的时序变化
   - Check the Testbench code to understand test cases and input timing

5. **运行测试** / **Run Test**
   - 点击 **"运行测试"**，程序自动编译并仿真你的代码与标准答案
   - Click **"Run Test"**; the app compiles and simulates both your code and the reference
   - 下方显示编译/运行状态和仿真输出
   - Compile/run status and simulation output are shown below

6. **查看波形** / **View Waveforms**
   - 测试成功后，点击 **"查看期望波形"** 和 **"查看你的波形"**，在 GTKWave 中对比
   - After a successful test, click **"View Expected Waveform"** and **"View Your Waveform"** to compare in GTKWave
   - 对比两个波形，找出不匹配的地方，返回修改代码
   - Compare the waveforms, find mismatches, then modify your code

7. **查看 RTL 视图** / **View RTL Diagram**
   - 点击 **"生成 RTL 视图"**，查看你的代码综合出的门级电路图（由 Yosys 生成，可拖拽缩放）
   - Click **"Generate RTL View"** to see the gate-level circuit synthesized from your code (generated by Yosys, draggable and zoomable)
   - 注意：只有可综合代码才能生成 RTL 图；含 `#延迟`、`initial` 的代码会报错，但这不影响仿真波形
   - Note: only synthesizable code can produce an RTL diagram; code with `#delay` or `initial` will fail — this does not affect simulation

8. **保存继续** / **Save and Continue**
   - 点击 **"保存并继续"** 进入下一题；最后一题将进入报告页
   - Click **"Save and Continue"** to go to the next question; the last question leads to the report page
   - 已尝试过的题目可以随时重新进入修改（重做），重新测试即可
   - Attempted questions can be reopened and modified at any time; just re-run the test

### 生成报告 / Generate Report

完成题目后：

After completing the questions:

1. 在周次页面点击 **"查看报告 →"** 进入报告页，程序会**自动生成最新报告**
   - On the Weeks page, click **"View Report →"** to open the report page; the app **automatically generates the latest report**
   - 无需点击任何按钮：每次进入报告页都会重新生成并覆盖旧报告，报告始终反映你的最新代码与测试结果
   - No button needed: every time you open the report page, it regenerates and overwrites the old report — the report always reflects your latest code and test results

2. 报告包含你的学号姓名、每题的题目描述、你的代码、测试结果，以及你的输出与标准答案的**逐时刻数值对比表**
   - The report contains your student ID and name, each question's description, your code, test results, and a **cycle-by-cycle value comparison table** between your output and the reference

3. 点击 **"打开文件位置"** 找到报告文件
   - Click **"Open File Location"** to locate the report file

4. 手动将报告文件提交到学校作业系统
   - Manually submit the report file to the school assignment system

5. 如果重做了某道题，重新进入报告页即可获得更新后的报告
   - If you redo a question, simply reopen the report page to get the updated report

### 查看数据目录 / View Data Directory

你的代码、进度和报告保存在以下位置（也可在"诊断"页查看具体路径）：

Your code, progress, and reports are stored at (also shown in the Diagnostics page):

| 平台 / Platform | 数据目录 / Data Directory |
|---|---|
| Windows | `C:\Users\<用户名>\AppData\Local\Verilog-Quiz` |
| macOS | `~/Library/Application Support/Verilog-Quiz` |
| Linux | `~/.local/share/verilog-quiz` |

目录结构 / Directory structure:

```
Verilog-Quiz/
├── questions/      # 下载的题目 / Downloaded questions
├── submissions/    # 你的代码和进度 / Your code and progress
├── reports/        # 生成的报告 / Generated reports
└── settings.json   # 学号等设置 / Settings (student ID, etc.)
```

---

## 故障排除 / Troubleshooting

### Q1: 诊断页显示 🔴 "未找到"工具

**A:**
1. 确认已按"准备工作"安装对应工具，并在终端中验证（如 `iverilog -V`）
2. 安装后**重新启动本程序**（PATH 变更需要重启才能生效）
3. 如果工具安装在非默认位置：打开"设置"页，在"工具路径"中手动填写可执行文件的完整路径，保存后回诊断页复查
4. **Windows 用户**：程序也支持自动使用 WSL 中安装的 iverilog/GTKWave/Yosys

### Q2: 无法连接到服务器 / 检查更新失败

**A:**
1. 检查网络连接是否正常
2. 在"设置"页点击 **"测试服务器连接"** 确认服务器状态
3. 已下载过的题目离线也能继续做，联网后重新"检查更新"即可
4. 联系助教确认服务器状态

### Q2b: 界面显示"本地后端已退出或无法连接"

**A:**

以下情况程序会**自动退出**（防止后台残留），均属正常设计：

- 关闭所有页面超过约 2 分钟；
- 电脑睡眠/锁屏超过约 2 分钟；
- 浏览器因内存不足自动卸载了长时间后台的标签页。

重新双击运行程序即可，代码和进度不会丢失（代码保存在磁盘上，与浏览器无关）。

The app **exits automatically** (to avoid background residue) when: all pages are closed for ~2 minutes, the computer sleeps for ~2 minutes, or the browser discards a long-inactive tab under memory pressure. This is by design. Just relaunch the app — your code and progress are preserved on disk.

### Q3: Windows 提示 "Windows 已保护你的电脑" (SmartScreen)

**A:**

点击 **"更多信息" → "仍要运行"**。本程序未购买商业代码签名，该提示属正常现象。

Click **"More info" → "Run anyway"**. The app is not commercially code-signed, so this prompt is expected.

### Q4: macOS 提示"无法打开，因为无法验证开发者"

**A:**

对程序图标 **右键 → 打开**，在弹窗中再点 **"打开"**（仅第一次需要）。

**Right-click → Open** on the app icon, then click **"Open"** in the dialog (only needed once).

### Q5: 编译失败，提示语法错误

**A:**
1. 仔细检查 Verilog 代码语法
2. 确保模块名、端口名与题目要求完全一致
3. 检查是否缺少分号 `;` 或括号不匹配
4. 参考 Testbench 中的端口定义

### Q6: RTL 视图生成报错

**A:**
1. RTL 视图只支持**可综合**的代码
2. 请移除 `#延迟`、`initial`、`$display` 等行为级语法（这些可以写在测试平台里，但不能写在你要提交的设计模块中）
3. 仿真波形不受影响，可继续用波形调试

### Q7: 波形对比发现不匹配

**A:**
1. 确认代码编译成功（无红色错误提示）
2. 同时打开 **"查看期望波形"** 和 **"查看你的波形"**，找出信号值或时序不一致的地方
3. 也可以生成 RTL 视图，检查你的电路结构是否符合预期
4. 返回修改代码后重新运行测试

### Q8: 如何向老师或助教求助？

**A:**
1. 打开"诊断"页，点击 **"复制诊断信息"**（包含系统、程序版本、各工具状态）
2. 粘贴到消息中发给老师或助教，并描述你进行的操作和看到的错误提示

---

## 获取帮助 / Getting Help

如果在使用过程中遇到任何问题，请：

If you encounter any issues during use, please:

1. 仔细阅读本手册相关章节 / Carefully check relevant sections of this manual
2. 查看程序界面的错误提示信息 / Check error messages in the application interface
3. 打开"诊断"页运行自检，并复制诊断信息 / Run self-check in the Diagnostics page and copy the diagnostics info
4. 向课程助教或老师寻求帮助 / Seek help from course TAs or instructors

---

祝学习顺利！/ Happy learning!
