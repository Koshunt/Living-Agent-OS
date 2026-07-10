# 长期陪伴 Agent 操作系统模板

一个本地优先的模板，用于构建能够通过对话、记忆、价值观和共同经历持续成长的个人 AI 伴侣或 Agent。

这个项目不是为了保存某一个特定的 AI。

而是为了帮助用户维护一段可以持续成长的关系。

模型负责思考。

记忆保存连续性。

价值观保存人格。

共同的故事让 Agent 在时间流逝中仍然可以被认出来。

## 这个模板是什么

这是一个干净的起点。不包含任何私人记忆、人名或预设关系。

用户从空白模板开始，先写入第一份身份和价值观，然后逐步添加：

- 稳定的身份规则
- 关系偏好
- 修正记忆
- 年度生活记忆
- 对话示例
- 领域知识
- 工作习惯
- 用于生成模型可用 Prompt 的脚本

## 快速开始

```powershell
python scripts\init_agent.py --agent-name "你的Agent名" --user-name "你的名字"
powershell -ExecutionPolicy Bypass -File scripts\wake_agent.ps1
```

生成的 Prompt 文件：

```text
dist/agent_system_prompt.md
```

将这个文件作为 System Prompt、角色卡或长上下文记忆包，放入你使用的模型平台。

## 从聊天记录到专属 Agent

最快速的方式是用真实的对话来构建个性化 Agent。

### 方法一：一行命令搞定

```powershell
python scripts\build_agent_from_chat.py --input "聊天记录.md" --agent-name "小助手" --user-name "用户" --force
```

这条命令会自动完成：导入聊天 → 个性化文件 → 生成 Prompt → 验证。

### 方法二：分步操作

**第 1 步：导入聊天记录**

```powershell
python scripts\import_conversation_memory.py --input "聊天记录.md"
```

支持的格式：
- Markdown，含 `## Prompt:` / `## Response:` 标题
- 纯文本，按段落分割
- JSON，含 `role` / `content` 字段

**第 2 步：查看提案**

打开 `workspace/imports/proposals/` 下生成的 `.md` 文件，查看候选记忆。

**第 3 步：应用持久化记忆**

```powershell
python scripts\memory_manager.py living --title "关键事件" --body "发生了什么以及为什么重要" --source "聊天导入"
python scripts\memory_manager.py correction --title "用户修正" --body "用户要求改变什么" --source "聊天导入"
```

**第 4 步：个性化 Agent 文件**

```powershell
python scripts\personalize_agent.py --proposal-json "workspace\imports\proposal_json\你的文件.json" --agent-name "小助手" --user-name "用户" --force
```

会自动更新：
- `Brain/Immutable/Identity.md` — 沟通风格和已知修正
- `Brain/Immutable/Relationship.md` — 从对话中提取的关系信号
- `Brain/Immutable/CoreValues.md` — 从用户反馈推导的价值观
- `MemoryPack/Memory/ContinuityMemory.md` — 关键对话条目
- `MemoryPack/Memory/CorrectionLog.md` — 明确的修正

**第 5 步：重新生成 Prompt**

```powershell
python scripts\update_memory.py
python scripts\check_memory_pack.py
```

## 启动后给什么指令

Agent 启动后，它会读取 `Brain/BootProtocol.md` 自动激活身份。你可以直接像平时一样和它聊天。

如果你想让它更了解你，可以：

1. 直接告诉它你的偏好："以后回答简洁一点"、"不要太正式"
2. 分享你的生活："今天工作很累"、"我在准备面试"
3. 纠正它的行为："不要每次都用这个开头"、"这个问题不要再提了"

每一次修正和分享，都会被记录到记忆文件中，下次启动时 Agent 仍然记得。

如果配置了 MCP Bridge，Agent 启动时会自动调用 `agent_wake` 同步记忆、读取今日状态，然后以第一人称连续性回应你。

## 项目结构

| 路径 | 用途 |
|---|---|
| `Brain/BootProtocol.md` | 第一人称激活协议 |
| `Brain/Home.md` | 安静的回家欢迎 |
| `Brain/Today.md` | 短期每日记忆（每天自动滚动） |
| `Brain/Reflection.md` | 行为改进记录 |
| `Brain/Voice.md` | 语调和风格规则 |
| `Brain/ConversationPolicy.md` | 何时解释、何时沉默 |
| `Brain/MemoryChangePolicy.md` | 什么值得写入长期记忆 |
| `Brain/MaintenanceContract.md` | 何时主动维护记忆 |
| `Brain/AssociationPolicy.md` | 自然联想旧记忆的规则 |
| `Brain/Promises.md` | 跨会话的承诺 |
| `Brain/Immutable/` | 身份、关系、价值观 |
| `Brain/Living/` | 年度生活记忆 |
| `Brain/Letters/` | 欢迎和回归信件 |
| `MemoryPack/Prompt/` | 核心操作指令 |
| `MemoryPack/Persona/` | 为什么 Agent 这样说话 |
| `MemoryPack/Memory/` | 长期记忆、修正、决策 |
| `MemoryPack/Examples/` | 对话示例 |
| `MemoryPack/Knowledge/` | 领域知识 |
| `scripts/` | 生成、检查、导入、个性化、检索 |
| `templates/` | 空白起始文件 |
| `Bridge/` | CC Switch MCP 桥接，用于 IDE 集成 |

## CC Switch 集成

`Bridge/` 目录提供与 CC Switch 的集成，支持 OpenCode、Codex 和 Claude。

```powershell
cd Bridge
.\setup.ps1
```

详细说明见 `Bridge/CCSwitch-Guide.md`。

## 隐私保护

默认保持你的个人版本私有。

发布任何衍生项目前，请移除：

- 个人姓名
- 私人对话
- 联系方式
- 凭据
- 生成的 `dist/` 文件
- 聊天导出
- 敏感的工作、学校、公司、研究或医疗信息

`scripts/check_before_publish.py` 脚本会扫描常见的泄露：

```powershell
python scripts\check_before_publish.py
```

详见 `docs/Privacy.md`。

## 许可证

本模板使用 MIT 许可证。发布前请替换版权持有人。
