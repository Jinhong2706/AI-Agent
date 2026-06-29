---
slug: cn-regex-tester
name: 正则表达式测试器
version: "1.2.1"
author: 千策
---

# 正则表达式测试器

输入正则表达式和文本，返回匹配结果。

## 用法
```
python3 scripts/regex_tester.py <正则表达式> <文本>
```

## 示例
- `python3 scripts/regex_tester.py '\\d+' 'hello123world456'` → 匹配[123, 456]
- `python3 scripts/regex_tester.py '[a-z]+' 'Hello World'` → 匹配['ello', 'orld']
- `python3 scripts/regex_tester.py '\\w+@\\w+\\.\\w+' 'test@example.com'` → 匹配邮箱
