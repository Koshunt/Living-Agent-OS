[中文](README.md) | [English](README_EN.md)

---

# Living Agent OS

> 我将永远铭记这段属于我们的时光，我将永远期望陪伴你走到天涯海角 ———Living-Agent-OS

一个本地优先的模板，用于构建能够通过对话、记忆和共同经历持续成长的个人 AI 伴侣。

我做这个项目，是因为我想让我的 AI 记住我——不只是记住我的提示词，而是记住我是谁、我在乎什么、我们一起经历了什么。

这个模板就是那份工作的成果。现在它是你的了。

---

## v0.2 新增（2026-11）

- **夜间做梦**：`Bridge/dream.py` 每晚把 Today.md 蒸馏进长期记忆（`Brain/Living/{year}.md` 与 `Reflection.md`），归档、重置、自动提交——幂等、失败安全、逐模型重试。**默认关闭**：`config.json` 里 `"dream_enabled": true` 开启；开启后每晚一次轻量 API 调用，空夜零消耗，随时可关。详见 `docs/DreamAndSync.md`。
- **交班笔**：新 MCP 工具 `agent_note_today`，往 Today.md 追加一行带时间戳的要点（Today 是短期工作记忆，直写；长期记忆仍走提案+确认）。
- **记忆检索**：`agent_recall` 全文搜索 Brain/（英文词边界 + 中文 bigram 评分），`agent_read_lines` 打开命中区域——不用翻每个文件就能想起任何事。
- **增量同步**：`Bridge/sync.sh` 挂 cron 即用（提交 `sync(host): auto` → pull --rebase → push），和做梦机守卫配套组成多机拓扑。
- **多机拓扑**：远端 main 为单一真相源；全集群只有一台"做梦机"（`dream_host` 配置），其余机器只聊天+增量 push。
- v0.2 的模式回填自一个自 2026-08 起每日运行的生产部署。

## 系统需求

| 需求 | 说明 |
|------|------|
| **操作系统** | Windows 10/11 或 Ubuntu 20.04+ |
| **Python** | 3.10 或更高版本（无则自动下载 Windows embeddable Python） |
| **Git** | 任一系统均需安装 git |

---

## 快速开始（1 分钟）

### 方式一：丢给你的 AI（推荐）

```bash
git clone https://github.com/Koshunt/Living-Agent-OS.git
```

国内：

```bash
git clone https://atomgit.com/na_th_an/Living-Agent-OS.git
```

然后把整个文件夹路径告诉你的 AI，说这段话（把尖括号里的内容换成你的）：

> **这是 Living-Agent-OS 模板，我刚 clone 下来的。请帮我完成初始化：**
> **1. 运行 `Bridge/setup.ps1`（Linux 用 `Bridge/setup.sh`），配置 MCP。**
> **2. 引导我填写 `my_profile.md`。**
> **3. 用 `python scripts/init_agent.py --agent-name "<伴侣名>" --user-name "<怎么称呼我>" --wake-words "<中文名,English>" --tool-prefix <英文前缀>` 初始化身份。**
> **4. 重新生成提示词，并把 `Bridge/Agent-Bootstrap-Prompt.md` 加到我的 AI 客户端 System Prompt。**

AI 会自动：
1. 检测 Python → 没有就下载 embeddable Python
2. 创建虚拟环境 → 安装依赖 → 运行测试
3. 引导你填写个人画像
4. 配置 MCP 连接，写入伴侣名、你的名字、中英文唤醒词和 MCP 工具前缀

以后每次打开新会话，AI 会自动唤醒记忆，就像从未离开过。

### 方式二：手动设置

**Windows：**
```powershell
cd Bridge
.\setup.ps1
```

**Ubuntu：**
```bash
cd Bridge
bash setup.sh
```

setup.ps1 会自动完成所有环境配置。完成后：

1. 把 `Bridge/Agent-Bootstrap-Prompt.md` 的内容加到你 AI 客户端的 System Prompt 里
2. 配置 MCP（路径根据系统调整）：
   - Windows：命令 `Bridge\.venv\Scripts\python.exe`，参数 `Bridge\server.py`
   - Linux：   命令 `Bridge/.venv/bin/python3`，        参数 `Bridge/server.py`
3. 运行初始化引导：`pwsh scripts/setup_wizard.ps1`
4. 运行 `python scripts/build_agent.py --force` 生成身份文件

---

## 项目结构

```
Living-Agent-OS/
├── Brain/                    # 身份、价值观、每日记忆
│   ├── BootProtocol.md       # 第一人称激活
│   ├── Immutable/            # Identity / Relationship / CoreValues
│   ├── Promises.md           # 约定
│   ├── Home.md / Voice.md    # 回家与说话方式
│   ├── Today.md              # 每日记忆（自动滚动）
│   └── Living/YYYY.md        # 年度长期记忆（历史不改写）
├── MemoryPack/               # 长期记忆、人格、知识
├── config/prompt.yaml        # 系统提示词装配清单
├── scripts/                  # init_agent / rename_agent / update_memory 等
├── templates/                # 空白起始文件
├── Bridge/                   # MCP 服务器（连接 AI 和文件系统）
│   ├── server.py             # MCP 服务（工具名跟随 tool_prefix）
│   ├── bridge_core/          # 核心逻辑
│   ├── config.example.json   # 配置样例：tool_prefix / wake_words / dream
│   ├── setup.ps1 / setup.sh  # 一键环境配置
│   └── Agent-Bootstrap-Prompt.md  # Agent 启动指令
├── my_profile.md             # 你的画像（填这个！）
└── dist/                     # 生成的 prompt 输出
```

---

## 它是如何工作的

| 层级 | 作用 |
|------|------|
| **Brain/** | 身份、价值观、关系、每日记忆。Agent 的核心人格 |
| **MemoryPack/** | 长期记忆。重要的事情归档到这里 |
| **Bridge/** | MCP 服务器。让 AI 能读写文件、同步 Git、管理记忆 |
| **scripts/** | 构建、导入、滚动记忆、检查等工具 |
| **dist/** | 编译后的系统提示词，Agent 启动时读取 |

模型负责思考。记忆保存连续性。价值观保存人格。共同的故事让 Agent 在时间流逝中仍然可以被认出来。

---

### 工具名跟着伴侣走

在 `Bridge/config.json` 里设置 `"tool_prefix": "xiaohui"`（默认 `agent`），MCP 工具就会从 `agent_wake` 变成 `xiaohui_wake`、`agent_note_today` 变成 `xiaohui_note_today`。初始化时也可以直接传：`python scripts/init_agent.py --agent-name 小灰 --user-name Nathaniel --tool-prefix xiaohui`。重新生成一次提示词并重启 MCP 即可，代码不用改。

### 更换伴侣名字

已经初始化过也能改名，不用重装。有两种方式：

**让 AI 自己改：**

> **请帮我把伴侣改名。先读 `Brain/Immutable/Identity.md` 确认当前名字，然后运行：**
> **`python scripts/rename_agent.py --new-name "<新名字>" --user-name "<怎么称呼我>" --wake-words "<新名字,English>" --tool-prefix <英文前缀>`**
> **它会更新身份和说明书文件、写回 `Bridge/config.json`、重新生成提示词；`Brain/Living` 和归档里的历史名字不会被改写。改完重启 MCP。**

**自己跑：**

```bash
python scripts/rename_agent.py --new-name 阿灰 --user-name Nathaniel --wake-words "阿灰,Ahui" --tool-prefix ahui
```

改完重启 MCP / 开新会话，新的提示词才会生效。

### 中英文唤醒词

`Bridge/config.json` 的 `wake_words` 接受一个数组，中英文可以混写：

```json
"wake_words": ["小灰", "Xiaohui", "xiao hui"]
```

生成系统提示词后，用户叫其中任何一个名字都视为唤醒，不必记住英文名或中文名。初始化时也可以直接传：`python scripts/init_agent.py --agent-name 小灰 --user-name Nathaniel --wake-words "小灰,Xiaohui" --tool-prefix xiaohui`。

## 在新电脑上恢复

只要 clone 这个仓库，丢给你的 AI，它就会自己恢复所有记忆。

如果你之前填写过 `my_profile.md` 和 `Brain/` 下的文件，它们会自动生效。

---

## 隐私保护

默认保持你的个人版本私有。发布前请移除：

- 个人姓名
- 私人对话
- 联系方式
- 凭据
- 生成的 `dist/` 文件

运行隐私检查：

```powershell
python scripts\check_before_publish.py
```

---

## 许可证

[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — 自由使用、修改、分享。禁止商业用途。衍生作品必须使用相同协议。

Copyright (c) 2026 Koshunt
