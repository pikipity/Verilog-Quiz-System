# Verilog 作业考试系统

一个单机版 Verilog 编程作业与考试系统，学生通过 GUI 界面完成编程题目，程序自动加密保护标准答案，生成 Markdown 格式报告供老师人工判卷。

## 功能特性

- **题目下载**：从远程服务器自动下载题目（支持 HTTP/HTTPS）
- **随机抽题**：每台机器固定随机种子，确保抽题结果一致
- **代码编辑**：内置代码编辑器，支持自动保存
- **仿真测试**：调用 iverilog 进行仿真，自动对比结果
- **波形显示**：可视化波形查看，支持 GTKWave 专业波形分析
- **报告生成**：自动生成 Markdown 格式报告，包含代码和测试结果
- **加密保护**：参考答案加密存储，防止作弊

## 系统要求

本程序运行需要以下依赖：

| 依赖 | 用途 | 必须 |
|------|------|------|
| **Icarus Verilog** | Verilog 代码编译和仿真 | 是 |
| **GTKWave** | 波形查看和分析 | 是 |
| **Python 3.8+** | 运行本程序 | 是 |

请根据你的操作系统，依次安装 **Icarus Verilog** 和 **GTKWave**：

### Windows

**Icarus Verilog（二选一）**

方案 A - 原生安装（推荐）：
1. 访问下载页面：https://bleyer.org/icarus/
2. 下载最新版本（如 `iverilog-v12-2024-12-16-x64.msi`）
3. 运行安装程序，按提示完成安装
4. 将安装目录（如 `C:\iverilog\bin`）添加到系统 PATH
5. 验证：`iverilog -v`

方案 B - WSL：
```powershell
wsl --install
wsl sudo apt-get update
wsl sudo apt-get install -y iverilog
```

**GTKWave**

1. 访问下载页面：https://gtkwave.sourceforge.net/
2. 下载 Windows 版本并安装到 `C:\Program Files\GTKWave`
3. 验证：`"C:\Program Files\GTKWave\bin\gtkwave.exe" --version`

WSL 用户也可在 WSL 中安装：
```bash
wsl sudo apt-get install -y gtkwave
```

### macOS

**Icarus Verilog**
```bash
brew install icarus-verilog
iverilog -v
```

**GTKWave**
```bash
brew install gtkwave
gtkwave --version
```

### Linux

#### Ubuntu / Debian

```bash
sudo apt-get update
sudo apt-get install -y iverilog gtkwave

# 验证
iverilog -v
gtkwave --version
```

#### CentOS / RHEL / Fedora

```bash
# Fedora
sudo dnf install -y iverilog gtkwave

# CentOS / RHEL
sudo yum install -y iverilog gtkwave

# 验证
iverilog -v
gtkwave --version
```

### Python 环境

- Python 3.8 或更高版本
- 推荐使用 [uv](https://github.com/astral-sh/uv) 或 [pip](https://pip.pypa.io/) 管理依赖

## 安装步骤

### 方法一：从源码运行（开发/调试）

1. **克隆仓库**
```bash
git clone https://github.com/yourusername/Verilog-Quiz-System.git
cd Verilog-Quiz-System
```

2. **创建虚拟环境（推荐）**

使用 uv：
```bash
uv venv
```

或使用 venv：
```bash
python -m venv .venv
```

3. **安装依赖**

使用 uv：
```bash
uv pip install -e .
```

或使用 pip：
```bash
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

4. **运行程序**

使用 uv：
```bash
uv run python main.py
```

或使用 Python：
```bash
python main.py
```

### 方法二：使用预编译可执行文件（推荐普通用户）

1. 从 [Releases](https://github.com/yourusername/Verilog-Quiz-System/releases) 页面下载对应平台的 zip 文件：
   - Windows: `verilog-quiz-windows.zip`
   - Linux: `verilog-quiz-linux.zip`
   - macOS: `verilog-quiz-macos.zip`

2. 解压 zip 文件到任意目录

3. **运行程序**：

   **Windows：**
   - 进入解压后的文件夹，双击 `verilog-quiz-system.exe` 运行

   **Linux/macOS：**
```bash
# 1. 进入解压后的目录
cd verilog-quiz-linux

# 2. 赋予执行权限
chmod +x verilog-quiz-system

# 3. 运行
./verilog-quiz-system
```

## 使用说明

### 首次使用

1. **启动程序**，进入周次选择界面
2. 点击 **"检查更新"** 从服务器下载题目
3. 选择题目周次，点击 **"开始"**

### 答题流程

1. **查看题目**：左侧显示题目描述
2. **编写代码**：在代码编辑器中编写 Verilog 代码（自动保存）
3. **查看测试平台**：了解测试用例和期望输出
4. **运行测试**：点击 **"运行测试"**，系统自动编译并对比结果
5. **查看波形**：测试完成后在 GTKWave 中查看波形，对比输入输出
6. **保存继续**：点击 **"保存并继续"** 进入下一题

### 数据存储位置

程序数据存储在用户目录下：

| 平台 | 数据目录 |
|------|---------|
| Windows | `C:\Users\<用户名>\AppData\Local\Verilog-Quiz\` |
| macOS | `~/Library/Application Support/Verilog-Quiz/` |
| Linux | `~/.local/share/verilog-quiz/` |

目录结构：
```
Verilog-Quiz/
├── questions/      # 下载的题目缓存
├── submissions/    # 学生代码和测试进度
└── reports/        # 生成的 Markdown 报告
```

### 生成报告

完成所有题目后：
1. 点击 **"生成报告"**
2. 报告将保存到 `reports/` 目录
3. 点击 **"打开文件夹"** 查看报告文件
4. 手动将报告提交到学校作业系统

## 服务器部署（教师端）

### 目录结构

```
/var/www/verilog-quiz/
├── manifest.json              # 全局清单
├── week1/
│   ├── info.json             # 周次配置
│   ├── q1/                   # 题目1
│   │   ├── question.md       # 题目描述
│   │   ├── testbench.v       # 测试平台
│   │   └── reference.v       # 参考答案
│   └── ...
└── week2/
    └── ...
```

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name quiz.example.com;
    root /var/www/verilog-quiz;
    
    location /verilog-quiz/ {
        alias /var/www/verilog-quiz/;
        autoindex on;
        
        # 跨域支持
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, OPTIONS";
        
        if ($request_method = OPTIONS) {
            return 204;
        }
    }
}
```

## 技术栈

- **GUI 框架**: [Flet](https://flet.dev/) (Flutter-based)
- **加密**: cryptography (XOR + Base64)
- **网络**: requests
- **仿真**: Icarus Verilog
- **波形查看**: GTKWave
- **打包**: PyInstaller

## 开发构建

### 本地打包

```bash
# 安装打包依赖
pip install pyinstaller

# Windows
pyinstaller --onefile --windowed --name verilog-quiz-windows main.py

# Linux
pyinstaller --onefile --name verilog-quiz-linux main.py

# macOS
pyinstaller --onefile --name verilog-quiz-macos main.py
```

### GitHub Actions 自动打包

本项目配置了 GitHub Actions，推送代码到 `main` 分支时自动构建：
- Windows (.exe)
- Linux
- macOS

构建产物自动发布到 [Releases](https://github.com/yourusername/Verilog-Quiz-System/releases) 页面。

## 常见问题

### Q: 提示"未检测到 iverilog"

**A:** 
1. 确认 iverilog 已正确安装
2. 确认 iverilog 在系统 PATH 中
3. Windows 用户可尝试 WSL 模式（程序会自动检测）

### Q: 提示"GTKWave not found" 或无法打开波形

**A:**
1. 确认 GTKWave 已正确安装（必须组件）
2. Windows 用户：确保安装在 `C:\Program Files\GTKWave\bin\gtkwave.exe`
3. 程序启动时会自动检测 GTKWave，可在控制台查看检测结果
4. 如未安装，请参考上文安装说明进行安装

### Q: 无法连接到服务器

**A:**
1. 检查网络连接
2. 确认 `config.py` 中的 `SERVER_URL` 配置正确
3. 确认服务器端 manifest.json 可访问

### Q: Linux/macOS 提示权限不足

**A:**
```bash
chmod +x verilog-quiz-system
```

### Q: 报告中的图片显示不正常

**A:** Markdown 报告中的图片使用相对路径，确保报告和图片在同一目录下。

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

**注意**: 本项目使用 Icarus Verilog 和 GTKWave 作为外部依赖，两者均采用 GPL 许可证。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

- 项目主页: https://github.com/yourusername/Verilog-Quiz-System
- 问题反馈: https://github.com/yourusername/Verilog-Quiz-System/issues
