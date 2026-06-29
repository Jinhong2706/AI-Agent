# 导出位置查看指南

表情包生成完成后，最终产物在哪里？如何打开查看？

---

## output 目录结构

所有生成产物位于用户"我的文档"目录下的 `~/Documents/wechat-sticker-output/` 目录中，按时间戳命名：

```
~/Documents/wechat-sticker-output/
└── 20260321_120000_gemini/       ← 时间戳 + 使用的 Provider
    ├── params.json               ← 配置参数
    ├── base_reference.png        ← 角色定妆图
    ├── anim_01/                  ← 第1个表情
    │   ├── original_grid.png     ← 宫格原图
    │   ├── origin/               ← 原图切片
    │   ├── nobg/                 ← 去背景版本
    │   └── animated_sticker.gif  ← 最终 GIF
    ├── anim_02/                  ← 第2个表情
    │   └── ...
    ├── ... (共24个 anim_XX 目录)
    └── wechat_export/            ← ⭐ 微信直接上传包
        ├── main/                 ← 01~24.gif (240x240 主图)
        ├── thumb/                ← 01~24.png (120x120 缩略图)
        ├── cover.png             ← 专辑封面 (240x240)
        ├── icon.png              ← 聊天页图标 (50x50)
        ├── banner.png            ← 详情页横幅 (750x400)
        └── upload_info.txt       ← 填单信息（名称、介绍、版权）
```

---

## 如何打开查看

### macOS - Finder 打开

```bash
# 进入输出目录
cd ~/Documents/wechat-sticker-output/20260321_120000_gemini

# 用 Finder 打开当前目录
open .
```

### macOS - 预览查看

```bash
# 预览封面
open wechat_export/cover.png

# 预览横幅
open wechat_export/banner.png

# 预览所有主图
open wechat_export/main/
```

### 命令行查看文件列表

```bash
# 查看 wechat_export 内容
ls wechat_export/

# 查看所有主图文件
ls wechat_export/main/

# 查看上传信息
cat wechat_export/upload_info.txt
```

### Windows

```bash
# 进入目录（我的文档）
cd %USERPROFILE%\Documents\wechat-sticker-output\20260321_120000_gemini

# 用资源管理器打开
explorer .
```

---

## wechat_export 目录说明 ⭐

**这是最重要的目录，包含可直接上传微信的全部产物。**

| 文件/目录 | 规格 | 说明 |
|----------|------|------|
| `main/` | 240x240 | 表情主图（PNG 或 GIF），编号 01~24 |
| `thumb/` | 120x120 | 表情缩略图，编号 01~24 |
| `cover.png` | 240x240 | 专辑封面，在表情商店展示 |
| `icon.png` | 50x50 | 聊天面板图标 |
| `banner.png` | 750x400 | 详情页横幅广告图 |
| `upload_info.txt` | 文本 | 名称、介绍（≤80字）、版权信息，可直接复制粘贴到微信后台 |

---

## 微信上传步骤

1. 打开微信表情开放平台：https://sticker.weixin.qq.com/
2. 创建新专辑
3. 从 `wechat_export/upload_info.txt` 复制名称、介绍、版权信息填入
4. 上传 `cover.png`、`icon.png`、`banner.png`
5. 上传 `main/` 目录下的所有主图
6. 上传 `thumb/` 目录下的所有缩略图
7. 提交审核

---

## 常见问题

**Q：找不到输出目录？**
A：输出目录位于"我的文档"：`~/Documents/wechat-sticker-output/`（macOS/Linux）或 `%USERPROFILE%\Documents\wechat-sticker-output\`（Windows）

**Q：wechat_export 目录不存在？**
A：需要运行 `python3 sticker_utils.py process $DIR_PATH` 才会生成

**Q：图片文件太大？**
A：微信主图限制 500KB，16帧 GIF 可能接近限制，可尝试减少帧数或简化动作