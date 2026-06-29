# 回放响应diff策略配置指南

LogReplay 支持配置 diff 策略来进行录制和回放响应数据的 diff，使回放报告的数据更精准，定位问题更高效、便捷。

# diff策略

支持可扩展的diff策略，粒度可以到字段级别，包括黑白名单、预处理策略、自定义对比策略、自定义脚本等

## 白名单

只对比白名单匹配的字段。

## 黑名单

不对比黑名单匹配的字段，如果某个字段白名单和黑名单都有，则为只对比白名单减掉黑名单中匹配的字段。

## 预处理策略

进行录制和回放响应数据diff前需要对响应JSON进行的操作，当前支持如下操作。

| 策略 | 策略类型 | 参数 | 示例 |
|------|----------|------|------|
| 以字符串形式存的 json 数组转换为数组 | `json-slice-to-slice` | | 处理前：`"[\"a\",\"b\",\"c\"]"` <br> 处理后：`["a", "b", "c"]` |
| 字符串转为数组 | `string-to-slice` | 分隔符，例如`","` <br> 排序规则（可选），asc/desc | 处理前：`"a, b, c"` <br> 参数：`","` <br> 处理后：`["a", "b", "c"]` <br><br> 处理前：`"3,1,2"` <br> 参数：`",", "asc"` <br> 处理后：`["1", "2", "3"]` |
| 字符串转为浮点数 | `string-to-float` | | 处理前：`"3.6"` <br> 处理后：`3.6` |
| 数组排序 | `slice-sort` | 排序规则，asc/desc <br> 排序依赖的字段，如id | 处理前：`[{"id": 2}, {"id": 1}]` <br> 参数：`"asc", "id"` <br> 处理后：`[{"id": 1}, {"id": 2}]` |
| 元素为字符串的数组展开为数组 | `slice-string-to-slice` | 要参与的字段，0表示所有字段 <br> 分割字段的分隔符 | 处理前：`["39\|0.9", "779\|0.7"]` <br> 参数：`"1,0", "\|"` <br> 处理后：`[["39", "0.9"], ["779", "0.7"]]` |
| 数组的字符串分隔符替换 | `slice-field-separator-replace` | 原分隔符 <br> 现分隔符 | 处理前：`["39\|ent", "779\|ent_china"]` <br> 参数：`"\|", ","` <br> 处理后：`["39,ent", "779,ent_china"]` |
| 空值转零值 | `nil-to-zero` | | 处理前：record: `{"a": 1, "b": 2, "c": 3}`, replay: `{"a": 1, "b": 2, "c": 3, "d": 4}` <br> 处理后：record: `{"a": 1, "b": 2, "c": 3, "d": 0}`, replay: `{"a": 1, "b": 2, "c": 3, "d": 4}` <br> 录制的数据中没有"d"，该策略会补充零值进行对比。<br> 支持的零值类型：bool→`false`，float→`0`，string→`""`，slice→`[]`，map→`{}` |
| 字符串转为map | `string-to-map` | | 处理前：`"{\"key\":\"val\"}"` <br> 处理后：`{"key": "val"}` <br> 将以字符串形式存储的 JSON 对象转换为 map |
| 字符串通过分割符切分为map | `split-string-to-map` | 元素分隔符 <br> 键值分隔符 | 处理前：`"key1:value1|key2:value2"` <br> 参数：`"|", ":"` <br> 处理后：`{"key1": "value1", "key2": "value2"}` <br> 值中包含键值分隔符时只按第一个分隔符切分，如 `"name:John:Doe"` → `{"name": "John:Doe"}` |
| json path 内容置空 | `json-path-content-set-nil` | | 处理前：`"you are handsome~"` <br> 处理后：`""` <br> 将匹配路径的字段内容置为该类型的零值（包括本层和子层），用于忽略特定字段的值差异 |
| 复杂嵌套结构的数组排序 | `complex-slice-sort` | 排序规则，asc/desc <br> 排序键路径，支持多级嵌套路径（用`.`分隔），支持多个排序键（用`,`分隔） | 处理前：`[{"info": {"score": 0.7}}, {"info": {"score": 0.9}}]` <br> 参数：`"desc", "info.score"` <br> 处理后：`[{"info": {"score": 0.9}}, {"info": {"score": 0.7}}]` <br><br> 多键排序示例：<br> 参数：`"desc", "recall_info.score,recall_info.extra_info.weight"` <br> 先按 `recall_info.score` 排序，相等时再按 `recall_info.extra_info.weight` 排序 |

## 自定义对比策略

进行录制和回放响应数据diff时可以选择自定义diff规则，以规则配置的参数来进行某个字段值的对比，当前支持如下自定义对比策略。

每种策略类型分为**流量对比**和**流量检查**两种模式：
- **流量对比**（策略类型：`string`、`float`、`set`、`map`）：需要录制和回放两条数据进行对比。
- **流量检查**（策略类型：`check-string`、`check-float`、`check-set`、`check-map`）：只需要录制或回放中的一条数据即可进行检查（取非空的一条），不需要两条数据进行对比。

> **注意：** 路径如果是正则的话，路径里如果有数组：比如data是个数组：`^responseBody.data\[\d\].distance`

| 值类型 | 策略类型 | 对比策略 | 对比/检查类型 | 参数 | 示例 |
|--------|----------|----------|---------------|------|------|
| string | `string` <br> `check-string` | 默认值 | `default` | 流量对比：录制的默认值、回放的默认值 <br> 流量检查：期望的默认值 | 流量对比：录制`"apple"` 回放`"orange"` 配置`"apple", "orange"` → true <br> 流量检查：流量值`"apple"` 配置`"apple"` → true |
|        |          | 正则匹配 | `regexp` | 匹配的正则表达式 | 流量对比：录制`"a.b.c.1"` 回放`"d.e.f.0"` 配置`"[a-z].[a-z].[a-z].[0-9]"` → true <br> 流量检查：流量值`"a.b.c.1"` 配置`"[a-z].[a-z].[a-z].[0-9]"` → true |
| float | `float` <br> `check-float` | 默认值 | `default` | 流量对比：录制的默认值、回放的默认值 <br> 流量检查：期望值条件表达式，如`"= 1.0"` | 流量对比：录制`1.0` 回放`2.0` 配置`1.0, 2.0` → true <br> 流量检查：流量值`1.0` 配置`"= 1.0"` → true |
|       |         | 浮动值 | `floating` | 两数之差除以较大数满足的条件，如`"< 0"` | 录制的值：`1.0` <br> 回放的值：`1.1` <br> 配置：`<= 0.1` <br> 结果：true |
|       |         | 差值 | `remainder` | 两数之差绝对值范围，如`"<= 1"` | 录制的值：`1.0` <br> 回放的值：`1.2` <br> 配置：`<= 0.2` <br> 结果：true |
|       |         | 组合 | `complex` | 组合策略 | 流量对比：录制`9.8` 回放`10.0` 配置`[floating, <= 0.02] & ([floating, > 0.1] \| [remainder, <= 0.2])` → true <br> 流量检查：流量值`10.0` 配置`[check-float, default, = 10.0]` → true |
| set | `set` <br> `check-set` | 无顺序相等 | `=` | 流量检查需传期望集合（JSON格式） | 流量对比：录制`[1, 2, 3, 4]` 回放`[2, 1, 4, 3]` → true <br> 流量检查：流量值`[1, 2, 3]` 配置`"=", "{\"data\": [3, 1, 2]}"` → true |
|     |     | 子集 | `<=` | 流量对比：回放包含录制 <br> 流量检查需传期望超集（JSON格式） | 流量对比：录制`[1, 2]` 回放`[1, 2, 3, 4]` → true <br> 流量检查：流量值`[1, 2]` 配置`"<=", "{\"data\": [1, 2, 3]}"` → true |
|     |     | 超集 | `>=` | 流量对比：录制包含回放 <br> 流量检查需传期望子集（JSON格式） | 流量对比：录制`[1, 2, 3, 4]` 回放`[3, 4]` → true <br> 流量检查：流量值`[1, 2, 3]` 配置`">=", "{\"data\": [1, 2]}"` → true |
| map | `map` <br> `check-map` | 相等 | `=` | 忽略map顺序 <br> 流量检查需传期望map（JSON格式） | 流量对比：录制`{"one": 1, "two": 2}` 回放`{"two": 2, "one": 1}` → true <br> 流量检查：流量值`{"a": 1, "b": 2}` 配置`"=", "{\"a\": 1, \"b\": 2}"` → true |

## 自定义 path 对比策略

支持配置自定义 path 对比策略，可以指定录制和回放数据中不同路径的字段进行对比。使用 JSONPath 语法（`$.`前缀）来定位字段。

例如，录制数据中的 `responseBody.data.name` 和回放数据中的 `responseBody.result.name` 进行对比：

```json
{
  "PathStrategy": [
    {
      "RecordPath": "responseBody.data.name",
      "ReplayPath": "responseBody.result.name"
    }
  ]
}
```

## 自定义脚本

LogReplay能够支持配置Python脚本进行录制和回放响应数据的diff，只需简单的Python基础即可上手使用。

```python
#!/usr/bin/python
# coding=utf-8

import sys
import json


def diff(arg1, arg2, arg3):
    req = json.loads(arg1)
    record = json.loads(arg2)
    replay = json.loads(arg3)

    # 请替换以下逻辑，完成record和replay的对比
    # 一致请返回"true,reason"，不一致请返回"false,reason"，reason可以是不包括英文逗号的任意字符串
    # reason建议使用"responseBody.A.B.0.C"格式 + 空格 + "added/deleted/modified"，方便定位问题
    if req["tag"] == "test" and (record["name"] != replay["name"]):
        return "false,name modified"
    return "true,success"


if __name__ == '__main__':

    msg = diff(sys.argv[1], sys.argv[2], sys.argv[3])

    print(msg)
```

# 字段匹配

上面所有的diff策略都是支持正则的，如果是简单的字段，可以直接写字段名，例如想匹配 `responseHeader` 中的 `time` 字段，那么可以写成：

```
responseHeader.time
```

但是如果响应体很复杂，嵌套很多，那么可以写正则表达式，但要注意正则表达式的正确性。

举个例子：如果想把 `responseBody.userInfo[*].userFollows` 这个字段加到黑名单不比对，那么正则表达式可以写成：

```
^responseBody\.userInfo\[\d+]\.userFollows
```
