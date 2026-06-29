---
name: xianyu-publish
description: 闲鱼自动发布技能。搜索同款商品图片、自动填表、发布二手回收帖。关键词：闲鱼、发布、二手回收、自动发布。
---

# xianyu-publish 闲鱼自动发布

## 快速开始

```
python main.py "小米14 95新 3999"
```

## 流程

```
输入商品描述 -> 自动识别品牌/型号/成色/价格 -> 搜索同款商品图片 -> 发布
```

## 文件说明

| 文件 | 作用 |
|------|------|
| main.py | 全自动入口 |
| login.py | 扫码登录，保存 Cookie |
| publish.py | 发布商品 |
| get_product_images.py | 搜索同款，下载图片 |
| product_info.py | 解析商品描述，自动补全信息 |
| stealth.py | 反检测引擎 |

## 使用步骤

### 1. 登录
```bash
python login.py
```
扫码后 Cookie 自动保存到 cookies.json。

### 2. 发布商品
```bash
python main.py "小米14 95新 3999"
python main.py "iPhone 15 Pro"
```
输入格式：品牌 型号 成色 价格（价格和成色可省略，系统自动估算）。

### 3. 单独发布（已有图片）
```bash
python publish.py --brand 小米 --model 小米14 --price 3999 --condition 95新 --images img1.jpg img2.jpg
```

## 常见问题

- 搜索无结果：账号限流，等几小时或手动登录闲鱼操作几下。
- 图片下载失败：CDN 请求失败时自动降级到缩略图。
- 发布按钮灰色：图片未上传成功，稍等重试。
- Cookie 失效：重新 python login.py。

## 注意

- 图片优先从详情页下载，要求自然宽 >= 400px
- 标题含坏机关键词（碎屏/进水/伊拉克等）自动跳过
- 浏览器窗口会自动打开（headless=False），操作期间不要关闭
