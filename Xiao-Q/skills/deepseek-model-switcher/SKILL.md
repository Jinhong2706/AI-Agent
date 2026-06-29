# Model Switcher 技能

## 功能
在 DeepSeek V4 Pro 和 DeepSeek V4 Flash 之间灵活切换当前会话的模型。

## 触发条件
当用户消息包含以下任一意图时触发：
- "切换pro" / "切Pro" / "换Pro" / "换V4 Pro"
- "切换flash" / "切Flash" / "换Flash" / "换V4 Flash"
- "切回去" / "换回去" / "切换回"（切换到 Flash）
- "切换模型到Pro/Flash"

## 执行流程
1. 判断用户意图（切换到 Pro 还是 Flash）
2. 调用 `session_status(model="deepseek/deepseek-v4-pro")` 或 `session_status(model="deepseek/deepseek-v4-flash")`
3. 回复确认：当前模型已切换为 XX，Token 成本约 XXX

## 模型信息
| 模型 | session_status 参数 | 特点 |
|:--|:--|:--|
| DeepSeek V4 Pro | `deepseek/deepseek-v4-pro` | 能力强，成本高 |
| DeepSeek V4 Flash | `deepseek/deepseek-v4-flash` | 速度快，成本低 |

## 注意事项
- 模型切换仅影响当前会话，不影响群聊其他会话
- 默认模型（default_model）不改变，仅覆盖本 session
- 切换后回复要简洁，体积感要轻
