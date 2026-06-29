# design-tokens.json Contract

`design-tokens.json` 是 **给代码和下游 Skill 读取的结构化设计源**。

它不是一份只有颜色和字号的普通 token 文件，而是一份最小可用的风格继承协议。

## 必须具备的顶层字段
- `meta`
- `style_summary`
- `layout`
- `colors`
- `typography`
- `spacing`
- `sizing`
- `radius`
- `borders`
- `shadows`
- `effects`
- `motion`
- `components`
- `imagery`
- `responsive`
- `constraints`
- `expansion_rules`

## 为什么必须有 `constraints`
因为 token 只给参数，不给边界时，下游 Skill 很容易：
- 用对了参数但做错了页面气质
- 改了布局密度
- 错用了阴影与渐变
- 把不该变化的组件重设计

因此必须用 `constraints.must_keep`、`constraints.may_adapt`、`constraints.must_not_do` 明确边界。
