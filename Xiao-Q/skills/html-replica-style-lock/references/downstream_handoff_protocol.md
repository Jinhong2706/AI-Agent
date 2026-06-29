# Downstream Handoff Protocol

当本 Skill 完成首个 HTML 基准页与风格锁定文件后，推荐下游 Skill 使用方式如下：

## 输入给 downstream Skill 的材料
- `index.html`
- `design-style-spec.md`
- `design-tokens.json`
- 用户新增页面需求

## 推荐使用对象
- `frontend-skill`
- 基于 `frontend-slides` 的页面生成 / 演示生成 Skill

## 建议追加给 downstream Skill 的要求

建议追加类似指令：

> 请严格基于已提供的 `index.html`、`design-style-spec.md` 与 `design-tokens.json` 扩展新页面。禁止自行替换颜色系统、字体层级、卡片质感、留白节奏、按钮语言、阴影逻辑、图像裁切方式与整体版式气质。允许调整内容组织，但不得改变视觉体系。

## 扩页时必须锁住的内容
- 主背景与叠层逻辑
- 标题层级与正文节奏
- 组件圆角、边框、阴影强度
- 卡片密度与留白规律
- 标签、按钮、导航的风格语言
- 图片裁切与遮罩方式
- 信息密度与页面语气

## 下游最容易跑偏的问题
- 无故换成另一套更“模板化”的字体
- 把留白做得更拥挤或更空
- 把克制阴影改成廉价阴影
- 把原图的高级灰/品牌色替换成更鲜艳的默认色
- 把简洁页面做成“科技感过重”或“营销感过强”
- 只读 token 不读 style spec，导致缺少设计意图

## 正确的角色分工
- 本 Skill：负责识别风格、锁定风格、做出首个 HTML 基准页
- downstream Skill：负责在已锁定风格的前提下扩展更多页面
