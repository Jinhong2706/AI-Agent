# 微信小程序开发助手

微信小程序开发的全流程助手——从 appid 申请、原生/Taro/uni-app 选型、云开发/自建后端选型,到登录鉴权、支付、订阅消息、审核避坑。区别于通用 Web 开发。

## 这是什么

`wechat-miniapp-zh` 是一个针对**中国本地场景**原创设计的 OpenClaw / SkillHub Agent Skill。
从问题定义、框架设计、示例都是为中国用户从零写的，不是任何已有项目的翻译或 fork。

## 触发场景

详见 `SKILL.md` 的 description 字段，AI 会自动判断何时调用。常见关键词：

- `微信小程序`
- `小程序开发`
- `Taro`
- `uni-app`
- `云开发`
- `wx.login`
- `微信支付`
- `订阅消息`
- `小程序审核`

## 安装

### SkillHub（推荐）

通过 SkillHub Web 界面安装：https://skillhub.cloud.tencent.com/skills/wechat-miniapp-zh

### OpenClaw / Claude Code

```bash
mkdir -p ~/.claude/skills
cp -R wechat-miniapp-zh ~/.claude/skills/wechat-miniapp-zh
```

### Cursor

把整个文件夹放到项目的 `.cursor/skills/wechat-miniapp-zh/` 下，重启 Cursor 即可。

## 用法

直接用自然语言描述需求，AI 会自动加载本 skill。例如：

```
帮我用 微信小程序开发助手 来 ...
```

## License

MIT © 2026 ikun

## 反馈

- 觉得有用：在 SkillHub 给个 star
- 报 bug / 建议：SkillHub 评论区留言
