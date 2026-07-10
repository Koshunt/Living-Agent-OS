[中文](CCSwitch-Guide.md) | [English](CCSwitch-Guide_EN.md)

# CC Switch 集成指南

这篇指南会一步步教你把 Agent OS 接入 CC Switch，让你的 Agent 能在 IDE 里读写记忆文件。

## 前置条件

- Windows 10/11
- Python 3.10+ 已安装并加入 PATH
- CC Switch 已安装（Chrome 扩展或桌面应用）
- 以下任一：OpenCode、Codex 或 Claude Desktop

---

## 第 1 步：运行安装脚本

在 `Bridge/` 文件夹下打开 PowerShell：

```powershell
cd Bridge
.\setup.ps1
```

脚本会自动：
1. 创建本地 Python 虚拟环境（`.venv/`）
2. 安装 MCP 依赖
3. 运行测试
4. 生成 `ccswitch-mcp-config.json`

如果脚本报错，先检查 Python 是否装好：`python --version`

---

## 第 2 步：在 CC Switch 中添加 MCP

1. 打开 CC Switch
2. 点击顶部的 **MCP**
3. 点右上角的 **+** 按钮
4. 选择 **自定义**

填写以下字段：

| 字段 | 填写 |
|------|------|
| MCP 标题（唯一） | `agent` |
| 显示名称 | `Agent OS` |
| 启用到应用 | ☑ OpenCode ☑ Codex ☑ Claude |

然后把 `ccswitch-mcp-config.json`（setup.ps1 自动生成的）的内容粘贴到配置区域。

---

## 第 3 步：添加启动提示词

1. 在 CC Switch 中，进入你用的应用（OpenCode / Codex / Claude）
2. 点击 **Prompts**
3. 新建一个 Prompt

| 字段 | 填写 |
|------|------|
| 名称 | `Agent OS Bootstrap` |
| 内容 | 粘贴 `Agent-Bootstrap-Prompt.md` 的全部内容 |

---

## 第 4 步：验证

重启 CLI，然后输入：

```
请先调用 agent_ping，然后告诉我当前 Agent OS 的 Git 状态。
```

如果 Agent 回复了 Git 状态信息，说明集成成功。

---

## 工作原理

```
你的 IDE ←→ CC Switch ←→ Bridge (Python) ←→ Agent OS 文件
```

- **agent_wake**：读取记忆文件，返回启动上下文
- **agent_read_memory**：按路径读取任意记忆文件
- **agent_write_memory**：写入内容到记忆文件
- **agent_git_status**：显示仓库的 Git 状态
- **agent_ping**：健康检查

---

## 常见问题

| 问题 | 解决方法 |
|------|----------|
| "command not found" | 确保 Python 在 PATH 中：`python --version` |
| MCP 连接失败 | 检查 CC Switch 是否运行，重启 CLI |
| Agent 没反应 | 检查 Prompt 是否正确粘贴到 CC Switch |
| 路径报错 | 编辑 Bridge 文件夹下的 `config.json`，设置正确路径 |

---

## 配置完成后的文件结构

```
Bridge/
├── config.json              # 你的本地路径（已 gitignore）
├── ccswitch-mcp-config.json # 给 CC Switch 用的（已 gitignore）
├── server.py                # MCP 服务器
├── core.py                  # Agent OS 操作
├── run_mcp.cmd              # 启动器
├── Agent-Bootstrap-Prompt.md # 粘贴到 CC Switch 的内容
└── CCSwitch-Guide.md        # 本文件
```
