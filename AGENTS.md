# Verilog作业考试系统 v2 - 项目方案

## 项目概述

单机版Verilog作业与考试系统。学生双击启动器后，程序在本机启动一个纯Python后端服务，并自动用默认浏览器打开界面。程序自动加密保护标准答案，调用iverilog进行仿真测试，调用Yosys生成RTL视图，生成PDF报告供老师人工判卷。

## v2 重构背景（为什么放弃 v1 架构）

v1 基于 Flet/Flutter 打包桌面应用，跨平台失败的根因：**分发的是构建产物，但运行时环境不受控**——Flutter 桌面壳依赖系统 GTK3/glibc（构建还需 clang/cmake/锁版 Flutter SDK），iverilog/GTKWave 由学生自行安装且安装状态各异。失败面是各层环境变量的乘积，无法靠测试覆盖。

v2 的核心原则：**把环境差异降到理论下限**

1. 分发的包只含 Python 运行时 + 静态文件，不链接任何系统 GUI 库；渲染交给浏览器（各平台最可靠的运行时）；
2. 后端零第三方 Python 依赖（仅用标准库），前端零构建步骤（原生 ES Modules + vendored 库）；
3. 外部工具（iverilog/GTKWave/Yosys）锁定版本、学生自装，程序负责三级探测、版本验证与功能自检；
4. 不再使用虚拟机，原生支持 Windows / macOS / Linux。

---

## 技术架构

| 组件 | 技术选择 | 说明 |
|------|---------|------|
| **GUI** | 学生默认浏览器 | 无构建原生 ES Modules SPA，第三方库全部 vendored 进包 |
| **后端** | Python 标准库 HTTP 服务 | ThreadingHTTPServer，只绑 127.0.0.1:随机端口，随机 token 鉴权 |
| **打包** | PyInstaller onedir | 四平台 CI 构建，零第三方 Python 依赖（不用 requests/cryptography/flet） |
| **题目分发** | HTTP 静态文件 | 服务器结构不变，与 V1 共用同一 manifest |
| **加密** | 内置密钥 + SHA256 派生 + XOR + Base64 | 不变，仅加密 reference.v（hashlib 标准库实现） |
| **仿真执行** | iverilog + vvp | 锁定版本，学生自行安装 |
| **波形查看** | GTKWave | 锁定版本，学生自行安装 |
| **RTL 视图** | Yosys write_json + netlistsvg | Yosys 锁版本学生自装；netlistsvg vendored，浏览器内渲染 SVG；仅对学生代码 |
| **报告** | PDF 本地生成（fpdf2 + 内嵌 Noto Sans CJK 字体） | 学生手动提交；Markdown 不落盘，仅内存中间态；内含数值对比表（仅供老师判卷） |

---

## 服务器端结构（不变）

```
https://your-server.com/verilog-quiz/
├── manifest.json                    # 全局清单（与 V1 共用，格式不变）
├── week1/
│   ├── info.json                    # 周次配置（id/folder 分离格式）
│   ├── q1/
│   │   ├── question.md              # 题目描述（含图片）
│   │   ├── testbench.v              # 测试平台
│   │   └── reference.v              # 标准答案（服务器端明文，见"URL混淆"节）
│   └── ...
└── ...
```

### manifest.json（与 V1 共用，schema_version 为可选）

```json
{
  "version": "1.0",
  "weeks": ["week1", "week2", "week3"]
}
```

**V1/V2 共用同一套题目与 manifest**，不要求新增任何字段。`schema_version` 是可选的：不存在时按 V1 格式处理（仅结构校验）；存在时必须是受支持的版本号，否则中止同步。中止条件：拉取失败、JSON 结构非法（非对象/weeks 缺失或格式错）、显式声明了不支持的 schema_version——任何中止都**不删除任何本地数据**。

### info.json 格式（不变）

```json
{
  "week": 1,
  "title": "组合逻辑电路基础",
  "updated_at": "2026-04-01T10:00:00",
  "questions": [
    {"id": "mux2to1_v1", "folder": "q1", "title": "2选1数据选择器"}
  ],
  "select_count": 2
}
```

**关键设计**（不变）：`id` 与 `folder` 分离。服务器端按 `folder` 组织文件，客户端下载后以 `id` 作为本地目录名。题目更新时可更换 `id` 而保持 `folder` 不变。

---

## 客户端目录结构

```
Verilog-Quiz-System/
├── main.py                          # 启动器：起本地服务、生成token、打开浏览器
├── config.py                        # 数据目录、锁定工具版本号、混淆后的服务器URL
├── backend/                         # HTTP层（纯标准库，无第三方依赖）
│   ├── app.py                       # 路由分发、token校验、静态文件托管
│   └── services/
│       ├── sync_service.py          # 题目对账同步（含week消失删除）
│       ├── yosys_service.py         # Yosys调用、RTL JSON生成
│       └── diagnostics.py           # 工具三级探测、版本验证、功能自检
├── core/                            # v1保留的核心资产
│   ├── crypto_manager.py            # 加密/解密（不变）
│   ├── question_manager.py          # 下载、加密存储（保留）；同步对账与学号抽题（重写）
│   ├── code_executor.py             # iverilog/vvp跨平台调用（基于tool_runner）
│   ├── tool_runner.py               # 跨平台命令执行（静默参数+重试），新增
│   ├── result_analyzer.py           # $display数值对比（供报告生成使用）
│   ├── report_generator.py          # 报告结构化内容（不落盘）
│   ├── pdf_generator.py             # PDF渲染（fpdf2+内嵌CJK字体），新增
│   └── gtkwave_helper.py            # GTKWave集成（平移）
├── assets/fonts/                    # vendored Noto Sans CJK SC（PDF用，OFL许可）
├── webui/                           # 前端静态文件（无构建步骤）
│   ├── index.html
│   ├── js/                          # 五个页面模块 + API封装 + hash路由
│   └── vendor/                      # codemirror6, marked, dompurify, netlistsvg, svg-pan-zoom
├── questions/  submissions/  reports/   # 数据目录（打包后位于平台数据目录，见config.py）
└── .github/workflows/               # PyInstaller四平台构建 + 无头冒烟测试
```

**已删除**：`ui/`（Flet界面层）、flet/flet-desktop 依赖、旧 Flutter 构建 workflow。

---

## API 设计（本地后端）

所有接口只监听 127.0.0.1，请求头需携带本次启动的随机 token。

| 端点 | 说明 |
|------|------|
| `GET /api/health` | 就绪探测（CI冒烟与前端轮询用） |
| `GET/PUT /api/settings` | 学号、姓名、工具路径覆盖 |
| `GET /api/tools/status` | 四工具三级验证结果（存在性/版本/自检） |
| `POST /api/tools/selfcheck` | 用内置最小样例做功能自检 |
| `POST /api/sync` | 检查更新+对账，返回变更摘要（新增/更新/移除） |
| `GET /api/weeks` | 周次列表+进度 |
| `GET /api/weeks/{n}/questions` | 抽中题目列表（含已尝试状态） |
| `GET /api/questions/{week}/{qid}` | 题面（图片base64内嵌）+ testbench |
| `GET/PUT /api/questions/{week}/{qid}/code` | 学生代码读取/保存 |
| `POST /api/questions/{week}/{qid}/test` | 编译+仿真学生与参考代码，写result.json |
| `GET /api/questions/{week}/{qid}/result` | 测试结果 |
| `POST /api/questions/{week}/{qid}/gtkwave?which=student\|ref` | 拉起GTKWave |
| `POST /api/questions/{week}/{qid}/rtl` | Yosys生成RTL JSON（或错误输出） |
| `POST /api/reports/{week}/generate` / `GET /api/reports/{week}` / `POST /api/reports/{week}/open_folder` | 报告生成/预览/打开位置 |
| `POST /api/open_data_folder` | 打开数据目录（顶部导航 Data Folder 按钮） |

---

## 核心流程

### 1. 首次启动流程

```
检测settings.json不存在 → 前端跳转设置页
  ↓
学生输入学号（必填）+ 姓名 → 保存settings.json
  ↓
工具检测（诊断页可查看三级验证结果，缺失给安装指引）
  ↓
触发题目同步 → 进入周次列表
```

### 2. 题目同步对账流程（v2 重写）

```
拉取 manifest.json
  ├─ 失败/超时/结构非法/schema_version不受支持 → 中止同步，不删任何本地数据，提示离线可用
  └─ 成功且校验通过
       ↓
对账：
  ├─ 本地有而服务器无的week → 删除 questions/weekN + submissions/weekN + reports/weekN_report.md
  ├─ 两边都有但 updated_at 更新 → 重下info.json，按学号种子对新id列表重算抽题；
  │    被移除题目连同其 submissions 删除；仍存在题目的学生代码保留
  └─ 服务器新增week → 抽题、下载、加密存储（同v1）
       ↓
返回摘要 → UI展示："新增 Week 3 / 更新 Week 1 / 移除 Week 2"
```

### 3. 学号抽题（v2 替换机器指纹）

- 种子：`SHA256(f"{student_id}_week{N}")`，完全确定——换电脑、重装系统结果不变；
- 首次启动在设置页录入学号，存 `settings.json`；
- **修改学号**：弹确认框，确认后清空 questions/submissions/reports 全部本地数据并重新同步（防共享电脑串数据）；
- 报告头部自动写入学号与姓名。

### 4. 答题流程

```
选择题目 → 加载题面（图片base64内嵌）+ 已存学生代码
  ↓
编辑代码（CodeMirror，Verilog语法高亮）→ 失焦+定时(30s)自动保存
  ↓
点击"运行测试" → 后端临时解密reference.v → 分别编译运行学生/参考代码
  ↓
生成各自VCD → 保存result.json → 清除内存与临时明文
  ↓
结果面板：编译/运行状态 + [查看期望波形] [查看你的波形] + RTL标签页
  ↓
"保存并继续"：跳转下一题（按列表顺序，与完成状态无关）；最后一题 → 跳转报告页
```

### 5. RTL 视图（v2 新功能）

- 后端执行：`yosys -p "read_verilog student.v; hierarchy -auto-top; proc; opt; write_json rtl.json"`；
- 前端用 netlistsvg 渲染为 SVG，svg-pan-zoom 支持缩放拖拽；
- **仅对学生代码生成；不提供参考代码的RTL视图**（门级结构图等同泄题）；
- 学生代码含 `#delay`、`initial` 等行为级语法时 Yosys 报错 → 前端展示原始错误输出，并提示"RTL视图仅适用于可综合代码，仿真波形不受影响"；
- 不使用 `yosys show`（依赖Graphviz，避免引入第四个外部工具）。

### 6. 重做机制

已尝试的题目可随时重新进入，加载已有代码，修改后自动覆盖保存，重新测试更新 result.json；重新进入报告页即重新生成报告。

**进度语义**：程序不判断"完成"（测试通过不等于做对，判卷由老师人工进行），只记录**已尝试/未尝试**——保存过非默认内容的代码即为"已尝试"。周次页与题目导航只显示已尝试状态。

### 7. 报告生成流程（PDF）

```
进入报告页 → 自动生成最新报告（覆盖旧报告，无需任何点击）
  ↓
report_generator 产出结构化内容（读取draw_result.json确定题目顺序，
  ↓  逐题整合题面+学生代码+测试结果+result_analyzer逐时刻数值对比）
pdf_generator 渲染（fpdf2 + 内嵌 Noto Sans CJK SC，GitHub 风格）
  ↓
生成 reports/weekN_report.pdf（Markdown 不落盘，仅内存中间态）
  ↓
页面内嵌 PDF 预览（浏览器原生阅读器）+ "Open File Location"
  ↓
学生手动将 PDF 提交到学校系统
```

**字形注意**：Noto Sans CJK SC 缺 ✗/❌/✅ 字形，PDF 中对比结果用 ✓/X 表示。

---

## 关键设计细节

### 本地服务安全

- 只绑定 `127.0.0.1`，端口由系统分配（`port=0`）；
- 每次启动生成随机 token，前端所有请求在 header 中携带，后端校验；
- 校验 Host 头，防 DNS rebinding；
- Windows 打包为 windowed 模式（无控制台窗口），日志写文件且脱敏。

### 生命周期（看门狗防残留）

- 前端每 10s 发送 `/api/heartbeat`；任何 API 调用都会刷新存活时间；
- 超过 120s 没有任何 API 活动（说明所有页面都已关闭）→ 后端自动退出，不产生后台残留进程；
- 超时取值必须大于浏览器对后台标签页定时器的节流上限（通常 60s），防止标签页仅在后台未关闭时被误杀；可用环境变量 `VERILOG_QUIZ_WATCHDOG_TIMEOUT` 覆盖（测试用）；
- 前端心跳连续失败 3 次 → 显示"后端已退出，请重新启动程序"遮罩。

### 代码持久化（重启不丢）

- 学生代码只存磁盘、不存浏览器：失焦 + 定时（30s）+ 运行测试前三重自动保存，经 API 写入 `submissions/weekN/{qid}/{qid}.v`；
- 数据目录（打包后）：Windows `%LOCALAPPDATA%\Verilog-Quiz`；macOS `~/Library/Application Support/Verilog-Quiz`；Linux `~/.local/share/verilog-quiz`；
- 重启电脑、换浏览器、清浏览器缓存均不丢代码；进度由磁盘 progress.json 恢复；
- 仅有的删除场景：week 从服务器消失（同步时删）、修改学号（确认后清空）——均有明示。

### 服务器URL客户端混淆

- URL 不以明文硬编码：拆段 + 编码存储，运行时拼装（二进制中 strings 搜不到明文）；
- 任何日志、API 返回值、界面均不出现 URL（v1 主界面底部曾直接展示，已移除）；
- 定位：防无意查看，不防专业破解（与加密策略同级）。

### 工具链管理：三级探测 + 三级验证

**三级探测**（定位可执行文件）：
1. 系统 PATH；
2. 常见安装目录（如 `C:\Program Files\GTKWave\bin\`）；
3. 设置页中用户手动指定的路径（解决"装到非标准位置检测不到"）。

**三级验证**（诊断页逐工具展示红绿灯）：
1. 存在性：三级探测是否找到；
2. 版本：运行 `-V`/`--version` 解析版本号，与锁定版本比对（绿=匹配，黄=不匹配但可用，红=未找到）；
3. 功能自检：点击"运行自检"，后端用**内置最小Verilog样例**（不依赖已下载题目）真实跑通 iverilog 编译 + vvp 仿真 + yosys JSON 生成；GTKWave 无法无头验证，提供"测试打开"按钮目视确认。

诊断页支持一键复制完整诊断信息（OS、程序版本、各工具版本与路径、自检结果），便于学生求助。

**锁定版本**（写入学生安装手册）：iverilog 11.0、GTKWave 3.3.104、Yosys 0.9——与老师验证环境（Ubuntu 22.04/WSL）一致，全部功能已在该组合实测通过。版本不符警告但不阻断。

### 加密策略（不变）

- 算法：SHA256(MASTER_KEY) 派生 32 字节密钥 → XOR 循环加密 → Base64 存储；
- 仅用 hashlib/base64 标准库实现（v1 的 cryptography 依赖未实际使用，已移除）；
- 仅加密 reference.v，下载时立即加密，使用时内存解密，明文不落盘。

### Windows 双模式（保留）

Windows 优先调用原生 iverilog/GTKWave，失败时 fallback 到 WSL（保留 v1 的路径转换逻辑）；安装手册只推原生安装。

### GTKWave 集成（不变）

平移 `gtkwave_helper.py`：解析 VCD 信号、自动生成 Tcl 脚本添加全部信号并缩放到合适视图；参考/学生波形分别对应 `ref_wave.vcd` / `student_wave.vcd`。

---

## 界面设计

**界面语言为英文**（含后端返回的所有用户可见文案）。五个页面（单页应用，hash 路由）：

1. **设置页**（Settings）：Student ID（必填）、Name、Tool paths（可选覆盖）、Test Server Connection；
2. **周次列表页**（Weeks）：周次卡片（Attempted 进度）、[Check Update] 按钮、同步摘要（Added/Updated/Removed）；顶部导航另有 [Data Folder] 按钮打开数据目录；
3. **答题页**（Question）：Question Description（Markdown 渲染含图片）、Code Editor（Verilog 高亮+行号）、Testbench 只读区、[Run Test] 与结果面板（点击后先清空旧结果显示"⏳ Running test, waiting for result…"再更新；含 View Expected/Your Waveform 两按钮）、RTL View 卡片、[Previous] [Save & Continue]；
4. **报告页**（Report）：进入即自动生成最新 PDF（无生成按钮）、浏览器内嵌 PDF 预览、[Open File Location]；
5. **诊断页**（Diagnostics）：工具三级验证表格（状态灯/Detected vs Pinned/Location）、[Run Self-Check]、[Test-launch GTKWave]、[Copy Diagnostics]。

---

## 分发形态

- 学生侧程序**免安装**：下载 zip → 解压 → 双击运行；Windows 无控制台窗口；
- Windows 未签名可能有 SmartScreen 提示（"更多信息→仍要运行"）；macOS 需右键打开一次（或 `xattr -dr com.apple.quarantine`）；均写入手册；
- 学生唯一需要安装的是三个外部工具（iverilog/GTKWave/Yosys 锁定版本）。

---

## 打包与 CI

- **PyInstaller onedir**（比 onefile 启动快、杀软误报少），zip 分发；
- **CI matrix**：`windows-latest`（x64）、`macos-14`（arm64）、`ubuntu-22.04`（x64）、`ubuntu-24.04-arm`；
- **无头端到端冒烟**（Web架构的红利）：每个平台产物启动后 `curl /api/health` 验证服务可用；Linux runner 上安装 iverilog+yosys，通过 API 无头跑完"同步→写码→仿真→RTL→报告"全流程；
- **分支分工**：
  - `push 到 dev / v2-rewrite`：四平台构建 + 冒烟 + 上传 artifacts，**不创建 Release**（仅验证打包流程，产物可从 Actions 页下载试跑）；
  - `push 到 main`（含 PR 合并）：四平台构建 + 冒烟 + 自动创建 GitHub Release 分发 zip；
  - 两分支均保留 workflow_dispatch 手动触发；
  - 冒烟逻辑在 `scripts/ci_smoke.py`（可本地复用），新增 week1 题目需在 CODE_MAP 中补充正确实现。

---

## 开发阶段（v2 里程碑）

| 里程碑 | 内容 | 验证目标 |
|--------|------|---------|
| **M1** | 删除 ui/ 与 Flet 依赖；后端骨架 + main.py 启动器 + PyInstaller + CI 冒烟 | 最先验证核心假设：四平台产物都能起服务、开页面 |
| **M2** | 对账同步 + 学号抽题 + 设置页 | week 消失/更新/新增场景全覆盖 |
| **M3** | 答题主流程（编辑器/仿真/波形/GTKWave） | 功能与 v1 持平 |
| **M4** | Yosys RTL 视图 | 新功能落地 |
| **M5** | 报告（含对比表）+ 诊断页 + 安装手册 + 端到端 CI | 可发布 |

**确认门**：M5 完成后先由项目维护者本机测试（按验收清单逐项确认），通过后再进行 workflow 打包改造，最终 PR 合入 main 触发发布构建。

---

## 部署清单

### 服务器端（不变）

- 静态文件服务，按周次组织题目文件夹（folder 名如 q1, q2）；
- 每道题：question.md、testbench.v、reference.v；
- manifest.json 与 info.json 格式均与 V1 一致，无需任何改动。

### 客户端

- 学生下载对应平台 zip，解压即用（无需 Python、无需虚拟机）；
- 自行安装锁定版本的 iverilog、GTKWave、Yosys（安装手册提供各平台图文指引）。

---

## 使用流程

### 老师视角（不变）

准备题目三件套 → 分配 id 放入 folder → 配置 info.json → 上传服务器 → 无需加密操作、无需服务器程序。

### 学生视角（v2）

1. 按手册安装锁定版本的 iverilog / GTKWave / Yosys；
2. 下载解压程序，双击运行，浏览器自动打开界面；
3. 首次启动输入学号姓名；诊断页确认四个工具全绿；
4. 检查更新下载题目，选择周次开始答题；
5. 编写代码（语法高亮），自动保存，运行测试查看状态；
6. 查看期望/自己的波形，查看自己代码的 RTL 视图；
7. 可随时重做已完成题目；完成后生成报告；
8. 手动将报告文件上传到学校作业系统。

---

## 本地开发指南

```bash
# 启动测试题目服务器（保持不变）
uv run python setup_test_server.py

# 开发模式运行主程序（同样起本地服务+自动开浏览器，无需打包）
uv run python main.py
```

- 前端开发：直接改 `webui/` 下文件，刷新浏览器即可，无构建步骤；
- 后端开发：改 `backend/`、`core/` 后重启 main.py；
- 重新测试下载流程：删除 `questions/` 内容（保留 .gitkeep）后重新同步。

### 常见问题

- **提示无法连接服务器**：确认测试服务器运行中；开发模式下 config.py 中的地址为明文（打包后混淆）；
- **诊断页工具红灯**：按手册安装锁定版本，或在设置页手动指定安装路径；
- **RTL 视图报错**：确认代码为可综合子集（无 `#delay`/`initial` 等行为级语法）。

---

## 技术约束与注意事项

1. **零第三方 Python 依赖原则**：后端仅用标准库（HTTP 用 http.server，网络用 urllib，加密用 hashlib）。已评估放行的例外：`fpdf2`（含 fonttools/pillow，纯 Python，用于 PDF 报告，PyInstaller 打包无原生风险）。再新增依赖需同样评估；
2. **前端零构建**：只允许原生 ES Modules + vendored 库，不引入 npm/打包器；
3. **URL 不明文**：服务器地址不得出现在明文源码、日志、API 返回、界面上；
4. **明文不落盘**：reference.v 仅在内存解密，临时文件用完即删；
5. **RTL 视图边界**：仅学生代码、仅可综合子集；报错时引导看波形；
6. **同步安全**：manifest 拉取失败或 schema 非法时必须中止同步，不得删除任何本地数据；
7. **威胁模型**：内置密钥与 URL 混淆防无意查看，不防专业破解，与 v1 一致；
8. **版本锁定**：iverilog/GTKWave/Yosys 手册指定小版本，程序检测到不匹配时警告但不阻断；
9. **子进程静默参数**：windowed 程序中所有 subprocess 调用必须用 `tool_runner` 的静默参数（stdin=DEVNULL、Windows 加 CREATE_NO_WINDOW），否则 wsl.exe 等控制台程序会间歇性报 0xc0000142；启动类错误重试一次。
