# 用户习惯学习规格

## 记忆层级

memory_layers:
  session_memory:
    scope: "当前会话"
    storage: "上下文变量"
    ttl: "会话结束消失"
    content: "[本次生成的正反向词/用户微调记录/即时偏好]"

  user_memory:
    scope: "跨会话用户级"
    storage: "MCP记忆功能 / 本地知识库"
    ttl: "永久（除非用户清除）"
    content: "[常用平台/默认风格/规避词/偏好参数/习惯表达]"

  global_memory:
    scope: "全局公共知识"
    storage: "RAG知识库"
    ttl: "长期"
    content: "[优质模板/平台特性/常见问题解决方案]"

## MCP记忆联动

mcp_integration:
  capability: "WorkBuddy平台提供MCP记忆功能"
  user_memory_store: "store_memory / recall_memory 工具"
  auto_sync: "每次用户确认满意 → 自动存入MCP"
  auto_recall: "用户再次来访 → 自动拉取偏好"

  memory_key_structure:
    prefix: "promptmaster_user_"
    fields:
      - "preferred_platform"
      - "default_style"
      - "avoid_keywords"
      - "quality_threshold"
      - "last_session_summary"

## 习惯学习时机

learning_trigger:
  explicit_learn:
    - "用户多次使用同一平台 → 记录为常用平台"
    - "用户反复指定同一风格 → 记录为默认风格"
    - "用户说「不要XXX」≥3次 → 记入规避清单"

  implicit_learn:
    - "连续3次微调方向一致 → 归纳为隐含偏好"
    - "从不选择某平台 → 推测为不喜欢（待确认）"

## 习惯应用

application:
  auto_fill: >
    用户再次生成时：
    - 自动填入常用平台（用户可修改）
    - 默认使用偏好风格（用户可拒绝）
    - 自动附加规避词（静默执行）

  confidence_boost: >
    命中用户习惯时：
    - 置信度+0.15
    - 可跳过部分调研环节
    - 减少正向词验证强度

## 用户控制

user_control:
  view_memory: "用户可输入「查看我的习惯」查看记录"
  clear_memory: "用户可输入「清除记忆」删除全部"
  update_memory: "用户可输入「修改习惯：XXX」更新特定项"
