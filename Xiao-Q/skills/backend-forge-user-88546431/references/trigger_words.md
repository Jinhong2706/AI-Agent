# Trigger Words

正式触发词：

- `bf-`
- `bf-fast`
- `bf-a`
- `bf a`
- `/backend-forge`

## 匹配规则

1. 触发词必须出现在用户消息首个 token 位置。
2. 触发词后必须是空白字符或字符串结束。
3. 代码块、URL、日志、文件名中的 `bf-` 不触发。
4. `bf-fast` 和 `bf-a` 是执行策略，不是独立任务模式。
5. 用户明确说“按 backend-forge 处理”也触发，即使没有短触发词。

## 非触发示例

```text
请解释 bf-a 是什么意思
```

```text
日志里有 bf-xxx
```

```text
https://example.com/bf-a
```

## 触发示例

```text
bf- 新建一个 FastAPI 项目
```

```text
bf-fast 修复这个接口报错
```

```text
bf a 给当前项目补健康检查和测试
```
