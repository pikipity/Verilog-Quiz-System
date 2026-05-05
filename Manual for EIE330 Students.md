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

---

## 支持的平台 / Supported Platforms

| 平台 / Platform | 支持状态 / Status | 推荐度 / Recommendation |
|---|---|---|
| Ubuntu 22.04 LTS | ✅ 完全支持 / Fully supported | ⭐⭐⭐⭐⭐ |
| Ubuntu 24.04 LTS | ✅ 完全支持 / Fully supported | ⭐⭐⭐⭐⭐ |

**特别提醒 / Special Note：**

本课程所有学生均使用 **VirtualBox + Ubuntu** 环境。请确保你的虚拟机系统为 **Ubuntu 22.04 LTS** 或 **Ubuntu 24.04 LTS**。

> 如果不熟悉 Linux 命令行或尚未安装操作系统，请参考 [Simple-VGA-Simulator 手册附录](https://github.com/pikipity/Simple-VGA-Simulator/blob/main/Manual%20for%20EIE330%20Students.md#10-%E9%99%84%E5%BD%95--appendices)：Appendix A（准备工作）和 Appendix B（系统安装）。

All students in this course use the **VirtualBox + Ubuntu** environment. Please ensure your virtual machine is running **Ubuntu 22.04 LTS** or **Ubuntu 24.04 LTS**.

> If you are not familiar with Linux command line or have not installed the operating system yet, please refer to the [Simple-VGA-Simulator Manual Appendices](https://github.com/pikipity/Simple-VGA-Simulator/blob/main/Manual%20for%20EIE330%20Students.md#10-%E9%99%84%E5%BD%95--appendices): Appendix A (Prerequisites) and Appendix B (System Installation).

---

## 准备工作 / Prerequisites

### 需要预装的软件 / Required Software

在使用本程序之前，你需要安装以下软件：

Before using this application, you need to install the following software:

| 软件 / Software | 用途 / Purpose | 安装说明 / Installation |
|---|---|---|
| **Icarus Verilog** | Verilog 仿真器 / Simulator | 见下方 / See below |
| **GTKWave** | 波形查看器 / Waveform viewer | 见下方 / See below |

### 安装 Icarus Verilog / Installing Icarus Verilog

```bash
sudo apt-get update
sudo apt-get install -y iverilog
```

### 安装 GTKWave / Installing GTKWave

```bash
sudo apt-get update
sudo apt-get install -y gtkwave
```

**验证安装 / Verify installation：**

```bash
# 验证 iverilog / Verify iverilog
iverilog -v
# 预期输出 / Expected: Icarus Verilog version 12.0 (stable)

# 验证 GTKWave / Verify GTKWave
gtkwave --version
# 预期输出 / Expected: GTKWave Analyzer version XXX
```

---

## 下载与运行 / Download and Run

### 从 GitHub 下载 / Download from GitHub

1. **访问 Releases 页面** / **Visit Releases page**
   - 打开：https://github.com/pikipity/Verilog-Quiz-System/releases
   - 找到最新版本（Latest）

2. **下载对应版本** / **Download for your platform**

   所有学生均在 VirtualBox + Ubuntu 环境中运行本程序，请根据你的宿主机系统选择对应的 Linux 版本：

   | 宿主机系统 / Host OS | 虚拟机架构 / VM Architecture | 下载文件 / Download File |
   |---|---|---|
   | Windows | x64 (Intel/AMD) | `verilog-quiz-linux.zip` |
   | macOS (Intel) | x64 (Intel) | `verilog-quiz-linux.zip` |
   | macOS (M 系列芯片 / Apple Silicon) | ARM64 | `verilog-quiz-linux-arm64.zip` |

3. **解压文件** / **Extract the zip**

   在 Ubuntu 终端中执行：

   ```bash
   unzip verilog-quiz-linux.zip
   ```

4. **运行程序** / **Run the application**

   ```bash
   # 1. 打开终端，进入解压后的目录 / Open terminal, navigate to extracted directory
   cd ~/Downloads/verilog-quiz-linux
   
   # 2. 赋予执行权限 / Add execute permission
   chmod +x verilog-quiz-system
   
   # 3. 运行 / Run
   ./verilog-quiz-system
   ```

---

## 使用教程 / Usage Tutorial

### 首次使用 / First Time Use

1. **启动程序** / **Launch the application**
   - 运行可执行文件，进入周次选择界面
   - Run the executable to enter the week selection interface

2. **检查更新** / **Check for updates**
   - 点击 **"检查更新"** 按钮从服务器下载题目
   - Click **"Check Update"** button to download questions from server
   - 如果提示连接失败，请检查网络或联系助教
   - If connection fails, check network or contact TA

3. **选择周次** / **Select week**
   - 下载完成后，会显示可用的周次列表
   - Available weeks will be displayed after download
   - 点击 **"开始"** 进入答题界面
   - Click **"Start"** to enter the question interface

### 答题流程 / Answering Process

1. **题目选择** / **Question Selection**
   - 界面顶部显示所有题目，可快速跳转
   - All questions displayed at top for quick navigation
   - 当前题目高亮显示，已完成的题目显示勾选标记
   - Current question highlighted, completed questions show checkmark

2. **查看题目** / **View Question**
   - 阅读题目描述，了解功能要求和端口定义
   - Read question description, understand requirements and port definitions
   - 查看端口定义表格，明确输入输出信号
   - Check port definition table for input/output signals

3. **编写代码** / **Write Code**
   - 在代码编辑器中编写 Verilog 代码
   - Write Verilog code in the code editor
   - 代码会自动保存（每30秒/失焦时/运行前）
   - Code auto-saves every 30 seconds, on focus out, and before run
   - 行号已显示，方便定位
   - Line numbers displayed for easy reference

4. **查看测试平台** / **View Testbench**
   - 查看 Testbench 代码，了解测试用例
   - Check Testbench code to understand test cases
   - 了解输入信号的时序变化
   - Understand timing changes of input signals

5. **运行测试** / **Run Test**
   - 点击 **"运行测试"** 按钮
   - Click **"Run Test"** button
   - 程序会自动编译你的代码并运行仿真
   - Application automatically compiles your code and runs simulation
   - 测试完成后弹出结果对话框
   - A result dialog appears after test completes

6. **查看结果** / **Check Results**
   - 测试成功后，对话框显示 **"Simulation Successful"**
   - On success, dialog shows **"Simulation Successful"**
   - 点击 **"View Expected Waveform"** 在 GTKWave 中查看期望波形（正确答案）
   - Click **"View Expected Waveform"** to open expected waveform in GTKWave
   - 点击 **"View Your Waveform"** 在 GTKWave 中查看你的实际波形
   - Click **"View Your Waveform"** to open your waveform in GTKWave
   - 对比两个波形，找出不匹配的地方，返回修改代码
   - Compare both waveforms, find mismatches, then return to modify code

7. **保存继续** / **Save and Continue**
   - 测试通过后，点击 **"保存并继续"**
   - After test passes, click **"Save and Continue"**
   - 进入下一题，或完成本周作业
   - Proceed to next question or complete weekly assignment

### 生成报告 / Generate Report

完成所有题目后：

After completing all questions:

1. 程序会提示 **"本周作业已完成！请生成报告。"**
   - Application prompts **"Weekly assignment completed! Please generate report."**

2. 点击 **"生成报告"** 按钮
   - Click **"Generate Report"** button

3. 报告将保存到系统应用数据目录：
   - Report saved to system application data directory:
   - `~/.local/share/verilog-quiz/reports/`

4. 点击 **"打开文件夹"** 查看报告
   - Click **"Open Folder"** to view report

5. 手动将报告文件提交到学校作业系统
   - Manually submit the report file to school assignment system

### 查看数据目录 / View Data Directory

如需查看或备份你的代码和进度：

To view or backup your code and progress:

1. 在周次选择界面点击 **"打开数据目录"**
   - Click **"Open Data Directory"** in week selection interface

2. 系统文件管理器会打开数据文件夹
   - System file manager opens the data folder

3. 目录结构：
   - Directory structure:
   ```
   Verilog-Quiz/
   ├── questions/      # 下载的题目 / Downloaded questions
   ├── submissions/    # 你的代码和进度 / Your code and progress
   └── reports/        # 生成的报告 / Generated reports
   ```

---

## 故障排除 / Troubleshooting

### Q1: 提示"未检测到 iverilog"

**A:**
1. 确认 iverilog 已正确安装：`iverilog -v`
2. 确认 iverilog 在系统 PATH 中
3. **Windows**: 尝试使用 WSL 模式（程序会自动检测）
4. **Linux**: 确认安装命令执行成功，尝试重新安装

### Q2: 无法连接到服务器

**A:**
1. 检查网络连接是否正常
2. 尝试在浏览器中访问服务器地址，确认服务器可用
3. 联系助教确认服务器状态

### Q3: Linux 提示权限不足

**A:**
```bash
# 赋予执行权限
chmod +x verilog-quiz-system

# 或者以管理员权限运行（不推荐）
sudo ./verilog-quiz-system
```

### Q4: 编译失败，提示语法错误

**A:**
1. 仔细检查 Verilog 代码语法
2. 确保所有模块名、端口名拼写正确
3. 检查是否缺少分号 `;` 或括号不匹配
4. 参考 Testbench 中的端口定义

### Q5: 提示 "GTKWave not found" 或无法打开波形

**A:**
1. 确认 GTKWave 已正确安装：`gtkwave --version`
2. **Windows**: 确保 GTKWave 安装在 `C:\Program Files\GTKWave\bin\gtkwave.exe`
3. **WSL**: 在 WSL 中执行 `sudo apt-get install -y gtkwave`
4. 程序启动时会在控制台显示 GTKWave 检测状态，请查看确认

### Q6: 波形图对比发现不匹配

**A:**
1. 确认代码编译成功（无红色错误提示）
2. 在 GTKWave 中同时打开 **View Expected Waveform** 和 **View Your Waveform**
3. 对比两个波形，找出信号值或时序不一致的地方
4. 检查 Testbench 中的端口连接是否正确
5. 返回修改代码后重新运行测试

### Q7: 报告生成失败

**A:**
1. 确认已完成所有题目（显示"已完成"状态）
2. 检查磁盘空间是否充足
3. 尝试手动创建 reports 目录
4. 查看程序是否有写入权限

---

## 获取帮助 / Getting Help

如果在使用过程中遇到任何问题，请：

If you encounter any issues during use, please:

1. 仔细阅读本手册相关章节 / Carefully check relevant sections of this manual
2. 查看程序界面的错误提示信息 / Check error messages in application interface
3. 检查终端/命令行的错误输出 / Check terminal/command line error output
4. 向课程助教或老师寻求帮助 / Seek help from course TAs or instructors

---

祝学习顺利！/ Happy learning!
