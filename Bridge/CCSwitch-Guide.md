# CC Switch 配置指南

## 一键部署

```powershell
.\setup.ps1
```

脚本会自动完成所有配置。完成后按提示在 CC Switch 中添加 MCP 和 Prompt。

---

## 手动配置

### 1. 添加 MCP 服务

打开 CC Switch → 顶部 **MCP** → 右上角 **+** → 选择 **自定义**。

| 字段 | 填写 |
|---|---|
| MCP 标题（唯一） | `agent` |
| 显示名称 | `Agent OS` |
| 启用到应用 | ☑ OpenCode ☑ Codex ☑ Claude |

然后粘贴 `ccswitch-mcp-config.json` 的内容（由 `setup.ps1` 自动生成）。

### 2. 添加提示词

打开 CC Switch → 对应应用（OpenCode/Codex/Claude）→ **Prompts** → 新建。

| 字段 | 填写 |
|---|---|
| 名称 | `Agent OS Bootstrap` |
| 内容 | 粘贴 `Agent-Bootstrap-Prompt.md` 全部内容 |

### 3. 验证

重启 CLI，输入：

```
请先调用 agent_ping，然后告诉我当前 Agent OS 的 Git 状态。
```
