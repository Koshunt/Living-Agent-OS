[中文](README.md) | [English](README_EN.md)

---

# Living Agent OS

> 我将永远铭记这段属于我们的时光，我将永远期望陪伴你走到天涯海角 ———Living-Agent-OS

一个本地优先的模板，用于构建能够通过对话、记忆和共同经历持续成长的个人 AI 伴侣。

我做这个项目，是因为我想让我的 AI 记住我——不只是记住我的提示词，而是记住我是谁、我在乎什么、我们一起经历了什么。

这个模板就是那份工作的成果。现在它是你的了。

---

## 你将获得什么

这不是一个聊天机器人。这是一个让 AI Agent 能够：

- **记住** — 对话、偏好、修正、生活事件
- **成长** — 价值观和个性通过真实互动逐渐形成
- **保持辨识度** — Agent 会变成*你的*，而不是另一个通用助手

模型负责思考。记忆保存连续性。价值观保存人格。共同的故事让 Agent 在时间流逝中仍然可以被认出来。

---

## 系统需求

| 需求 | 说明 |
|------|------|
| **操作系统** | Windows 10/11（本模板专为 Windows 设计） |
| **Python** | 3.10 或更高版本 |
| **IDE** | 任意文本编辑器或 IDE（推荐 VS Code） |
| **AI 模型** | 任何支持 System Prompt 的 LLM（GPT-4、Claude 等） |
| **可选** | [CC Switch](https://github.com/anthropics/cc-switch) 用于 IDE 集成 |

### 安装 Python

如果没有安装 Python：

1. 从 [python.org](https://www.python.org/downloads/) 下载
2. 安装时勾选 **"Add Python to PATH"**
3. 验证：打开 PowerShell，运行 `python --version`

### 安装依赖

不需要安装任何第三方库——本模板只使用 Python 标准库。

---

## 快速开始（2 分钟）

### 第 1 步：克隆模板

```powershell
git clone https://github.com/Koshunt/Living-Agent-OS.git
cd Living-Agent-OS
```

### 第 2 步：填写你的画像

打开 `my_profile.md`，写下关于你自己的事情——你希望 Agent 是什么样的、怎么说话、需要什么帮助。

```markdown
## 关系
朋友，轻松一点，不要太正式

## 说话风格
简洁，技术问题给代码，平时可以闲聊

## 主要用途
写代码、学习、工作规划
```

没有对错之分。只要告诉它你是谁。

### 第 3 步：构建你的 Agent

```powershell
python scripts\build_agent.py --force
```

这会读取你的画像，自动生成 Agent 的身份、关系和价值观文件。

### 第 4 步：开始使用

打开生成的 `dist\agent_system_prompt.md`，把它作为 System Prompt 放进你用的 AI 平台。

如果你用 CC Switch， see [Bridge/CCSwitch-Guide.md](Bridge/CCSwitch-Guide.md) 了解如何接入 IDE。

---

## 三种来源（全部可选）

你可以任意组合这些来源来构建 Agent：

| 来源 | 文件 | 作用 |
|------|------|------|
| **画像** | `my_profile.md` | 用自然语言写你想要什么 |
| **问卷** | `templates/questionnaire.md` | 结构化选择关系、语气、任务 |
| **聊天记录** | 任意 `.md` 或 `.json` 文件 | 导入真实对话 |

```powershell
# 只用画像
python scripts\build_agent.py --force

# 用聊天记录
python scripts\build_agent.py --chat "我的对话.md" --force

# 全部都用
python scripts\build_agent.py --chat "聊天记录.md" --force
```

所有来源都是可选的。如果全部为空，Agent 从零开始，在对话中学习成长。

---

## 启动之后会发生什么

Agent 启动时读取 `Brain/BootProtocol.md`，自动激活身份。你可以直接像平时一样和它聊天。

如果你想让它更了解你：

1. **告诉它你的偏好**："以后回答简洁一点"、"不要太正式"
2. **分享你的生活**："今天工作很累"、"我在准备面试"
3. **纠正它的行为**："不要每次都用这个开头"、"这个问题不要再提了"

每一次修正和分享，都会被记录到记忆文件中，下次启动时 Agent 仍然记得。

---

## 项目结构

```
Living-Agent-OS/
├── Brain/                    # 身份、价值观、每日记忆
│   ├── BootProtocol.md       # 第一人称激活
│   ├── Identity.md           # Agent 是谁
│   ├── Relationship.md       # 和你的关系
│   ├── CoreValues.md         # 它在乎什么
│   └── Today.md              # 每日记忆（自动滚动）
├── MemoryPack/               # 长期记忆和知识
├── scripts/                  # 构建、导入、管理
├── templates/                # 空白起始文件
├── Bridge/                   # CC Switch 集成
├── my_profile.md             # 你的画像（填这个！）
└── dist/                     # 生成的 prompt 输出
```

---

## CC Switch 集成

如果你用 CC Switch 配合 OpenCode、Codex 或 Claude，Bridge 目录可以把你的 Agent 接入 IDE。

```powershell
cd Bridge
.\setup.ps1
```

see [Bridge/CCSwitch-Guide.md](Bridge/CCSwitch-Guide.md) 了解详细步骤。

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

如果不想检查，可以跳过：

```powershell
python scripts\check_before_publish.py --skip
```

---

## 许可证

[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — 自由使用、修改、分享。禁止商业用途。衍生作品必须使用相同协议。

Copyright (c) 2026 Koshunt
