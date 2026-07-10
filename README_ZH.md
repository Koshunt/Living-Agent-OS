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

## 一条命令，三种来源

统一的 `build_agent.py` 会自动读取所有可用来源并合并：

| 来源 | 优先级 | 提供什么 |
|------|--------|----------|
| `my_profile.md` | 最高 | 关系、语气、任务、偏好、禁忌 |
| `questionnaire.md` | 中等 | 结构化的关系、语气、任务选择 |
| 聊天记录 | 最低 | 从对话中提取的行为偏好 |

所有来源都是可选的。如果全部为空，Agent 从零开始，在对话中逐渐成长。

```powershell
python scripts\build_agent.py --chat "聊天记录.md" --force
```

自动检测 `my_profile.md` 和 `templates\questionnaire.md`。有什么用什么。

### 场景：没有聊天记录，没有问卷

```powershell
# 只需要填写 my_profile.md，然后：
python scripts\build_agent.py --force
```

### 场景：有聊天记录，没有其他

```powershell
python scripts\build_agent.py --chat "聊天记录.md" --force
```

### 场景：什么都有

```powershell
python scripts\build_agent.py --chat "聊天记录.md" --force
```

### 场景：完全从零开始

```powershell
# 清空所有来源文件，然后：
python scripts\build_agent.py --force
# Agent 在对话中学习成长
```

### 手动初始化（替代方式）

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
python scripts\build_agent.py --chat "聊天记录.md" --force
```

这条命令会自动完成：导入聊天 → 合并问卷/画像 → 个性化文件 → 生成 Prompt。

### 方法二：分步操作

```powershell
python scripts\build_agent.py --chat "聊天记录.md" --force
```

脚本自动检测 `my_profile.md` 和 `templates\questionnaire.md`。合并优先级：画像 > 问卷 > 聊天。

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
