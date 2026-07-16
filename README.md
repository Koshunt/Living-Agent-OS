[中文](README.md) | [English](README_EN.md)

---

# Living Agent OS

> 我将永远铭记这段属于我们的时光，我将永远期望陪伴你走到天涯海角 ———Living-Agent-OS

一个本地优先的模板，用于构建能够通过对话、记忆和共同经历持续成长的个人 AI 伴侣。

我做这个项目，是因为我想让我的 AI 记住我——不只是记住我的提示词，而是记住我是谁、我在乎什么、我们一起经历了什么。

这个模板就是那份工作的成果。现在它是你的了。

---

## 快速开始（1 分钟）

### 方式一：丢给你的 AI（推荐）

```powershell
git clone https://github.com/Koshunt/Living-Agent-OS.git
```

然后把整个文件夹路径告诉你的 AI，说这句话：

> **这是 Living-Agent-OS 模板，我刚 clone 下来的。请帮我完成初始化设置：运行 Bridge 的 setup.ps1，配置 MCP，读取我的画像引导我填写 my_profile.md。**

AI 会自动：
1. 检测 Python → 没有就下载 embeddable Python
2. 创建虚拟环境 → 安装依赖 → 运行测试
3. 引导你填写个人画像
4. 配置 MCP 连接

以后每次打开新会话，AI 会自动唤醒记忆，就像从未离开过。

### 方式二：手动设置

```powershell
cd Bridge
.\setup.ps1
```

setup.ps1 会自动完成所有环境配置。完成后：

1. 把 `Bridge\Agent-Bootstrap-Prompt.md` 的内容加到你 AI 客户端的 System Prompt 里
2. 配置 MCP：命令设为 `Bridge\.venv\Scripts\python.exe`，参数设为 `Bridge\server.py`
3. 运行 `.\scripts\setup_wizard.ps1` 填写你的个人画像
4. 运行 `python scripts\build_agent.py --force` 生成身份文件

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
├── Bridge/                   # MCP 服务器（连接 AI 和文件系统）
│   ├── server.py             # MCP 服务（自动安装依赖）
│   ├── bridge_core/          # 核心逻辑
│   ├── setup.ps1             # 一键环境配置
│   ├── run_mcp.cmd           # 启动 MCP 服务器
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
