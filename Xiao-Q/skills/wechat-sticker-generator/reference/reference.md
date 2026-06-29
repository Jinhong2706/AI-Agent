# WeChat Sticker Generator — 参数参考文档

> 本文件供人类阅读，包含所有参数选项、算法原理和使用示例。Agent 执行流程见根目录 `SKILL.md`。

---

## 配置方式

### 方式一：环境变量（推荐）

```bash
export GEMINI_API_KEY="你的API_Key"
export DASHSCOPE_API_KEY="你的API_Key"
```

### 方式二：配置文件

| 系统 | 路径 |
|------|------|
| macOS/Linux | `~/.sticker_generator_config.json` |
| Windows | `C:\Users\你的用户名\.sticker_generator_config.json` |

```json
{
  "default_provider": "gemini",
  "providers": {
    "gemini": { "api_key": "你的Key" },
    "qwen": { "api_key": "你的Key" }
  }
}
```

> ⚠️ 请勿在对话中直接提供 API Key。

---

## 风格预设 (style_preset) {#style_preset}

| 选项 | 风格描述 | 适用场景 |
|------|----------|----------|
| `2D_KAWAII` (默认) | 日系二次元，圆润可爱 | 通用，最推荐 |
| `2D_ANIME_COOL` | 日系帅气，锐利线条 | 少年向、热血 |
| `3D_CLAY` | 3D黏土质感，柔软立体 | 儿童、萌系 |
| `3D_PIXAR` | 皮克斯风格，欧美3D | 欧美风、全年龄 |
| `PIXEL_ART` | 16bit像素风，复古游戏 | 极客、游戏 |
| `CHINESE_INK` | 中国水墨风，淡雅意境 | 国风、文艺 |
| `WATERCOLOR` | 水彩手绘风，温柔治愈 | 文艺、清新 |
| `LINE_ART` | 极简黑白线条，手绘涂鸦 | 极简风 |
| `CARTOON_WEST` | 美式卡通，夸张变形 | 搞笑、欧美 |
| `CHIBI_SD` | Q版SD比例，头大身小 | 萌系、游戏 |
| `MEME_STYLE` | 表情包网红风，魔性夸张 | 搞笑、网络流行 |
| `CUSTOM` | 自定义（填写 custom_style） | 特殊需求 |

---

## 场景主题 (scene_theme) {#scene_theme}

用户可自由描述任意场景，也可使用以下预设：

| 选项 | 微信后台分类 | 配文参考 |
|------|-------------|----------|
| `COMPREHENSIVE` | 综合 | 日常百搭 |
| `FESTIVAL` | 节日节气 | 新年快乐、生日快乐 |
| `ROMANCE` | 恋爱交友 | 想你、爱你、晚安 |
| `GREETING` | 祝福问候 | 早安、谢谢、对不起 |
| `WORKPLACE` | 职场工作 | 收到、下班、KPI |
| `STUDY` | 毕业/学生 | 加油、不想学、求过 |
| `GAMING` | 游戏电竞 | 胜利、GG、上号 |
| `PETS` | 动物萌宠 | 萌喵、傻犬 |
| `FOOD` | 饮食吃饭 | 饿了、奶茶、大餐 |
| `SPORTS` | 运动健身 | 冲刺、流汗、健身 |

---

## 角色类型 (character_type) {#character_type}

| 选项 | 类型 | character_prompt 示例 |
|------|------|----------------------|
| `HUMAN_CHIBI` | Q版人类 | "戴眼镜短发女生，蓝色卫衣，圆脸大眼" |
| `HUMAN_ANIME` | 日系动漫 | "银色长发少女，红瞳，哥特萝莉装" |
| `ANIMAL_CUTE` | 可爱动物 | "橘猫，胖乎乎，大眼睛，尾巴翘起" |
| `ANIMAL_ANTHRO` | 拟人动物 | "穿西装的兔子先生，戴礼帽" |
| `FANTASY` | 奇幻生物 | "小精灵，透明翅膀，发光，飘浮" |
| `OBJECT_PERSONIFIED` | 拟人物品 | "有表情的饭团，三角形，海苔脸" |
| `IP_CHARACTER` | 知名IP | "皮卡丘，黄色电气鼠，红脸颊，闪电尾巴" |

---

## 配色氛围 (color_mood) {#color_mood}

| 选项 | 色调 |
|------|------|
| `BRIGHT_VIBRANT` (默认) | 明亮鲜艳，高饱和度 |
| `SOFT_PASTEL` | 柔和粉彩，马卡龙 |
| `WARM_COZY` | 暖色调，温馨 |
| `COOL_CALM` | 冷色调，沉稳 |
| `MONOCHROME` | 黑白单色 |
| `NEON_CYBER` | 霓虹赛博，荧光 |
| `VINTAGE_RETRO` | 复古怀旧，褪色感 |

---

## 宫格配置 (grid_size) {#grid_size}

| grid_size | 布局 | 帧数 | GIF 时长 | 适用 |
|-----------|------|------|----------|------|
| `9` (默认) | 3×3 | 9帧 | 0.9秒 | 标准，速度快 |
| `16` | 4×4 | 16帧 | 1.6秒 | 动作更细腻 |

- 静态模式：每个宫格包含 9 或 16 张独立静态表情。微信专辑标准需 **24 张**，需生成 3 个 9宫格或 2 个 16宫格。
- 动态模式：每个宫格对应 **1 个 GIF**。微信专辑标准需 **24 个 GIF**，需生成 24 个宫格图（`anim_01` 到 `anim_24`）。
- 微信主图文件大小限制 **500KB**，16帧 GIF 通常在范围内。

---

## 背景去除算法 (bg_removal_method) {#bg_removal}

| 方法 | 处理方式 | 适用场景 |
|------|----------|----------|
| `opencv` | 整图一次性，漫水填充 + 柔和 Alpha | 深色前景 + 纯白背景；文字边缘最优 |
| `rembg` | 切片后逐格深度学习抠图 | opencv 失败时兜底；可能误删文字 |
| `dual` (推荐) | 两者同时运行，取 Alpha 最大值 | 浅色前景（水墨/水彩/像素）+ 保护文字 |

**风格推荐映射：**

| 风格 | 推荐方法 |
|------|----------|
| `CHINESE_INK` / `WATERCOLOR` / `PIXEL_ART` | `dual` |
| `3D_CLAY` / `3D_PIXAR` / `CHIBI_SD` | `dual` |
| `2D_KAWAII` | `dual` 或 `opencv` |
| `MEME_STYLE` | `opencv` |

**自动降级**：opencv 检测到背景非纯白时自动切换 rembg，无需人工介入。

---

## 动作描述指南 {#action-guide}

**公式：夸张身体姿态 + 面部表情变化 + (可选)道具/特效**

✅ 好的描述：
- "向后仰头大笑，笑到眼泪飞溅，肚子剧烈颤抖"
- "整个人趴在地上打滚，四肢乱蹬，撒泼耍赖"
- "双手捂脸从指缝偷看，身体扭成麻花状"

❌ 避免：
- "微笑"（太静止）
- "开心地看着"（缺乏动作）
- "做出生气的表情"（幅度太小）

---

## 完整示例 {#example}

### 用户请求
> "帮我做一套打工人表情包，角色是一个秃头程序员大叔，要动态的，搞笑一点"

### params.json

```json
{
  "mode": "animated",
  "set_name": "秃头小猿",
  "set_description": "每天修Bug、抗击KPI的卑微打工人日常，虽然头秃但依然坚强！",
  "copyright_info": "李强制作",
  "character_name": "秃头猿",
  "character_prompt": "中年秃头程序员大叔，圆脸，稀疏头发，戴厚底黑框眼镜，穿皱巴巴格子衬衫，黑眼圈很重，一脸疲惫但眼神呆萌",
  "reference_image": "$DIR_PATH/base_reference.png",
  "style_preset": "MEME_STYLE",
  "custom_style": "",
  "scene_theme": "WORKPLACE",
  "character_type": "HUMAN_CHIBI",
  "color_mood": "BRIGHT_VIBRANT",
  "background_type": "transparent",
  "enable_bg_removal": true,
  "bg_removal_method": "dual",
  "bg_removal_model": "isnet-anime",
  "bg_alpha_matting": true,
  "bg_sharpen_edges": false,
  "bg_sharpen_threshold": 200,
  "grid_size": 9,
  "expressions": [
    {"action": "疯狂敲键盘到手指冒烟，眼睛瞪得像铜铃，整个人变成残影", "text": "搬砖"},
    {"action": "看到代码报错，整个人石化碎裂成渣，眼珠子弹出来", "text": "寄!"},
    {"action": "下班时间一到，瞬间变身火箭冲出办公室，留下一道残影", "text": "润了"},
    {"action": "收到甲方需求，整个人瘫倒在桌上，眼睛变成死鱼眼", "text": "好累"},
    {"action": "开会被点名，满头大汗，两只手不知道往哪放", "text": "慌了"},
    {"action": "摸鱼被抓包，表情僵硬，嘴角抽搐，冷汗直流", "text": "完了"},
    {"action": "看到工资条，眼睛变成金钱符号，整个人飘起来", "text": "真香"},
    {"action": "老板走近工位，立刻切换屏幕，假装认真工作", "text": "装忙"},
    {"action": "项目上线成功，双手比V，跳起来庆祝，周围飘彩带", "text": "成了"}
  ]
}
```

---

## 真人照片转 Q 版 {#photo-chibi}

```bash
python3 sticker_utils.py transform_photo <photo_path> <style_preset> <output_path> [additional_description]
```

| 原照片类型 | 推荐风格 |
|-----------|----------|
| 普通人像 | `2D_KAWAII` |
| 男生照片 | `2D_ANIME_COOL` |
| 儿童照片 | `3D_CLAY` |
| 情侣照片 | `2D_KAWAII` |
| 游戏玩家 | `PIXEL_ART` |
| 搞笑表情 | `MEME_STYLE` |

Gemini 自动处理：主角识别 → 风格转换 → 特征保留（脸型/发型/眼镜等）→ 输出 512×512 白底图。
