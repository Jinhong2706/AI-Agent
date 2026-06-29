---
name: wechat-sticker-generator
description: 一键生成符合微信规范的动态(GIF)及静态(PNG)系列表情包套件。支持12种画风、10大场景主题、真人照片转Q版，全自动切割合成标准产物。
version: 1.0.3
author: 七天
license: MIT
tags:
  - wechat
  - sticker
  - image-generation
  - gif
  - emoji
  - animation
keywords:
  - 表情包
  - 动图
  - GIF生成
  - 微信贴纸
  - Q版角色
  - 真人转Q版
triggers:
  - "表情包"
  - "动图"
  - "贴纸"
  - "sticker"
  - "做表情"
metadata:
  openclaw:
    requires:
      env:
        - GEMINI_API_KEY
        - DASHSCOPE_API_KEY
      anyBins:
        - python3
        - python
    primaryEnv: GEMINI_API_KEY
    emoji: "🎭"
    homepage: https://github.com/sterlingdon/wechat-sticker-generator
    install:
      - kind: pip
        package: rembg==2.0.75 onnxruntime==1.24.4 pillow==12.1.1 requests==2.32.5 google-genai==1.68.0 dashscope==1.25.15
---

# WeChat Sticker Generator（微信表情包套件生成器）

> 参数选项完整表格（风格/场景/角色类型/配色）→ 见 [`reference/reference.md`](reference/reference.md)

---

## ⚠️ 运行前提：所有命令必须在 skill 根目录下执行

```bash
ls sticker_utils.py   # 能看到这个文件才能继续
```

---

## ⚡ 第一件事：检测 API Key 与 Provider

```bash
python3 sticker_utils.py config
```

- **显示 ✅ GEMINI** → 进入**完整流水线**，后续命令使用 `--provider gemini`
- **显示 ✅ QWEN（千问）** → 进入**完整流水线**，后续命令使用 `--provider qwen`
- **显示 ❌** → 进入**手动流程**（跳到文末），并告知用户配置方式：
  - Gemini：`export GEMINI_API_KEY="你的Key"`（推荐，效果更好）
  - 千问：`export DASHSCOPE_API_KEY="你的Key"`（国内访问稳定）

> 后文中凡出现 `--provider <PROVIDER>`，请替换为上面检测到的实际值（`gemini` 或 `qwen`）。

---

## 两种模式说明（必读，决定后续所有操作）

| 对比项               | `static`（静态）                           | `animated`（动态GIF）                       |
| -------------------- | ------------------------------------------ | ------------------------------------------- |
| **每次生成什么**     | 一张宫格图 → 切出 9 或 16 张**独立静态图** | 一张宫格图 → 合成 **1 个 GIF**（9帧或16帧） |
| **expressions 含义** | 每个 expression = 1 张独立表情             | 每个 expression = GIF 的 1 帧动作           |
| **子目录命名**       | `static_01/`, `static_02/`...              | `anim_01/`, `anim_02/`...                   |
| **主图文件类型**     | `.png`                                     | `.gif`                                      |
| **微信专辑需 24 个** | 3 次循环（9宫格）或 2 次循环（16宫格）     | 24 次循环，每次生成 1 个 GIF                |
| **默认值**           | ✅ 默认                                    | 需用户明确选择                              |

**⚠️ 后文所有涉及子目录的地方：静态模式用 `static_XX`，动态模式用 `anim_XX`。**

---

## 完整流水线（有 API Key）

### 【步骤 0】收集用户需求（开始任何操作前必须完成，不可跳过）

> **⛔ 硬性规则：未收齐以下所有信息，绝对不允许执行任何命令。不得自行填写默认值替代用户回答。**

**逐项向用户提问，每项未得到明确回复前不得跳过，不得假设。** 可以多问几轮，直到下方 8 项全部收到用户的明确答复为止。

---

**需要逐一询问的 8 项信息：**

**①** 有没有定妆图？（定妆图 = 白底纯背景、正面姿势的角色基准图；没有也没关系，用文字描述也可以）

**②** 角色外观描述是什么？（如：橘色短发、穿蓝色卫衣的女生，越详细越好）

- 若①有定妆图，此项可选；若①没有定妆图，此项**必须提供**

**③** 角色名称叫什么？（选填，没有可以跳过）

**④** 想要什么画风？请从以下选择，或说"默认"：

- `2D_KAWAII`（萌系Q版，**默认**）、`2D_ANIME_COOL`（帅气动漫）、`3D_CLAY`（黏土玩具）
- `3D_PIXAR`（皮克斯3D）、`PIXEL_ART`（像素风）、`CHINESE_INK`（水墨国风）
- `WATERCOLOR`（水彩插画）、`LINE_ART`（简笔线条）、`CARTOON_WEST`（欧美卡通）
- `CHIBI_SD`（超级Q版）、`MEME_STYLE`（表情包梗图风）、`CUSTOM`（自定义，需另说明）

**⑤** 想要什么场景主题？可从以下列表选择，或直接描述自定义主题（如"宇宙星空"、"猫咖下午茶"），或说"默认"：

- `COMPREHENSIVE`（综合全能，**默认**）、`WORK_OFFICE`（职场打工）、`LOVE_ROMANCE`（爱情恋爱）
- `FOOD_LIFE`（吃货日常）、`FESTIVAL`（节日庆典）、`STUDY_EXAM`（学习备考）
- `SPORT_FITNESS`（运动健身）、`TRAVEL`（旅行探险）、`GAMING`（游戏电竞）
- `PET_ANIMAL`（萌宠动物）；**或自由填写任意主题描述**

**⑥** 想要静态图还是动态GIF？

- `static`（静态图集，**默认**，生成9或16张独立PNG）
- `animated`（动态GIF，每个GIF由9或16帧组成）

**⑦** 宫格类型选几格？（**默认9格**；16格动作更流畅但生成时间较长）

**⑧** 需要几个表情？（**默认9个**；微信专辑标准需24个）

---

**收齐全部 8 项后，向用户做一次汇总确认，得到"确认"或"开始"后，才可进入步骤 1。**

---

### 【步骤 1】创建沙盒目录

```bash
DIR_PATH=$(python3 sticker_utils.py create_dir --provider <PROVIDER>)
echo "沙盒目录：$DIR_PATH"
```

执行后得到一个带时间戳的工作目录路径。**记住这个路径**，后续所有步骤都会用到 `$DIR_PATH`。

---

### 【步骤 2】处理定妆图（必须产出 $DIR_PATH/base_reference.png）

**⚠️ 核心规则：所有表情生成都依赖 `$DIR_PATH/base_reference.png`，本步骤必须产出该文件，否则无法继续。**

根据用户情况，选且只选一个操作：

**情况 A：用户提供了定妆图文件路径**

```bash
cp "<用户提供的路径>" "$DIR_PATH/base_reference.png"
```

**情况 B：用户在对话中直接上传了图片**

```bash
cp "<上传图片的路径>" "$DIR_PATH/base_reference.png"
```

**情况 C：用户提供了参考图（非标准定妆图，需要 AI 转换）**

```bash
cp "<用户参考图路径>" "$DIR_PATH/user_reference.png"
python3 sticker_utils.py draw_with_ref "$DIR_PATH/user_reference.png" "<角色外观描述>" "<STYLE_PRESET>" "$DIR_PATH/base_reference.png"
```

**情况 D：用户提供了真人照片，要转成 Q 版**

```bash
cp "<用户照片路径>" "$DIR_PATH/user_photo.jpg"
python3 sticker_utils.py transform_photo "$DIR_PATH/user_photo.jpg" "<STYLE_PRESET>" "$DIR_PATH/base_reference.png"
```

**情况 E：用户只有文字描述，无任何图片**

```bash
python3 sticker_utils.py draw_character "<角色外观描述>" "<STYLE_PRESET>" "$DIR_PATH/base_reference.png"
```

**执行完后必须验证文件存在：**

```bash
ls -lh "$DIR_PATH/base_reference.png"   # 必须能看到此文件，否则重新执行本步骤
```

---

### 【步骤 3】写入 params.json

**⚠️ 写入前的三条硬性规则：**

1. `reference_image` 字段必须是 `base_reference.png` 的**真实完整路径**（不是变量名，是实际路径字符串）
2. `expressions` 数组长度必须严格等于 `grid_size`：选了 9 就写 9 条，选了 16 就写 16 条
3. 每个 `action` 必须包含大幅度身体动作（见下方动作规则），不能是"微笑"这类静止描述

**⚠️ 注意：下方 heredoc 使用 `<< EOF`（无引号），`$DIR_PATH` 才会正确展开为真实路径。**

```bash
cat > "$DIR_PATH/params.json" << EOF
{
  "mode": "static",
  "set_name": "表情包名称",
  "set_description": "套件描述（不超过80字）",
  "copyright_info": "版权信息",
  "character_name": "角色名称",
  "character_prompt": "角色外观描述（只写外观，不写动作）",
  "reference_image": "$DIR_PATH/base_reference.png",
  "style_preset": "2D_KAWAII",
  "custom_style": "",
  "scene_theme": "COMPREHENSIVE",
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
    {"action": "动作描述1（必须大幅度身体运动）", "text": "配文1（2-4字）"},
    {"action": "动作描述2", "text": "配文2"},
    {"action": "动作描述3", "text": "配文3"},
    {"action": "动作描述4", "text": "配文4"},
    {"action": "动作描述5", "text": "配文5"},
    {"action": "动作描述6", "text": "配文6"},
    {"action": "动作描述7", "text": "配文7"},
    {"action": "动作描述8", "text": "配文8"},
    {"action": "动作描述9", "text": "配文9"}
  ]
}
EOF
```

> 如果选了 `grid_size: 16`，`expressions` 必须补充到 16 条。

**写入后验证（两个数字必须相同）：**

```bash
python3 -c "import json; d=json.load(open('$DIR_PATH/params.json')); print('✅ expressions数量:', len(d['expressions']), ' grid_size:', d['grid_size'])"
```

**动作描述规则（每个 action 必须遵循）：**

公式：**夸张身体姿态 + 面部表情变化 + (可选)道具/特效**

✅ 正确：`"向后仰头大笑，笑到眼泪飞溅，肚子剧烈颤抖"`、`"整个人趴在地上打滚，四肢乱蹬"`

❌ 错误（会产生"面瘫"表情包）：`"微笑"` / `"开心地看着"` / `"表示同意"`

---

### 【步骤 3 附：动态模式（animated）循环说明】

> **仅当 `mode` 为 `animated` 时需要阅读本节。静态模式跳过。**

**animated 模式每次执行步骤 3→6 只生成 1 个 GIF。** 微信专辑需要 24 个 GIF，因此必须循环 24 次。

**每次循环的操作：**

1. 修改 `params.json` 中的 `expressions`，改为下一个 GIF 的 9（或16）帧动作描述
2. 重新执行步骤 4（`build_prompts`）、步骤 5（`batch_draw`）、步骤 6（`process`）
3. 系统自动将新生成的 GIF 存入 `anim_02/`、`anim_03/` 等递增编号目录

**循环计数建议：**

```
第 1 次循环 → 产出 anim_01/animated_sticker.gif
第 2 次循环 → 产出 anim_02/animated_sticker.gif
...
第 24 次循环 → 产出 anim_24/animated_sticker.gif
```

**所有 24 次循环完成后**，再执行步骤 7（`wechat_meta`），最终 `wechat_export/main/` 汇总所有 GIF。

---

### 【步骤 4】解析配置（生成各表情的 Prompt 文件）

```bash
python3 sticker_utils.py build_prompts $DIR_PATH
```

- **static 模式**：在 `$DIR_PATH/static_01/`、`static_02/`... 下生成 `prompt.txt`
- **animated 模式**：在 `$DIR_PATH/anim_01/`、`anim_02/`... 下生成 `prompt.txt`

---

### 【步骤 5】批量生图

```bash
# 顺序执行（推荐，保证角色一致性）
python3 sticker_utils.py batch_draw $DIR_PATH
```

可选并发（可能影响角色一致性，慎用）：

```bash
python3 sticker_utils.py batch_draw $DIR_PATH --concurrent 2 --delay 3.0
```

**⚠️ 如果 API 调用中途失败：**

1. 检查哪些子目录下还没有 `original_grid.png`（已有的会自动跳过）
2. 对缺失的子目录，让用户手动在外部平台生图（操作见 `reference/external_platform_guide.md`）
3. 用户返回图片后，放入对应目录：
   - static 模式：`cp "<图片路径>" "$DIR_PATH/static_XX/original_grid.png"`
   - animated 模式：`cp "<图片路径>" "$DIR_PATH/anim_XX/original_grid.png"`
   - （XX 替换为对应编号，如 01、02）
4. 重新运行 `batch_draw`，已有图片的目录自动跳过，只补全缺失的

---

### 【步骤 6】去背景与切片

```bash
python3 sticker_utils.py process $DIR_PATH
```

**产出说明（以 animated 模式 anim_01 为例，static 模式同理但目录名为 static_XX）：**

- `$DIR_PATH/anim_01/origin/`：原图切片（仅裁剪缩放，无去背）
- `$DIR_PATH/anim_01/nobg/`：透明背景版（去背成功时额外生成）
- `$DIR_PATH/anim_01/animated_sticker.gif`：合成的 GIF（**仅 animated 模式有此文件**）
- `$DIR_PATH/anim_01/original_grid_nobg.png`：整图去背预览

**背景去除方法（在 params.json 的 `bg_removal_method` 中配置）：**

| 值                   | 适用场景                                            |
| -------------------- | --------------------------------------------------- |
| `dual`（默认，推荐） | 水墨风、水彩风、像素风、Q版等浅色前景；同时保护文字 |
| `opencv`             | 深色前景 + 纯白背景；文字边缘质量最优               |
| `rembg`              | opencv 失败时的兜底选项；可能误删文字               |

---

### 【步骤 7】生成微信物料（⚠️ 必须执行，不可跳过）

**重要：步骤 6 的 `wechat_export/` 里的 banner 和 cover 只是占位图，不能直接用。必须执行本步骤用 AI 重新生成高质量版本。**

```bash
python3 sticker_utils.py wechat_meta $DIR_PATH
```

本步骤产出（覆盖步骤 6 的占位内容）：

| 产物                            | 规格    | 说明                            |
| ------------------------------- | ------- | ------------------------------- |
| `wechat_export/banner.png`      | 750×400 | AI 专属绘制横幅                 |
| `wechat_export/cover.png`       | 240×240 | AI 专属绘制封面                 |
| `wechat_export/icon.png`        | 50×50   | 聊天面板图标                    |
| `wechat_export/upload_info.txt` | 文本    | ≤80字介绍 + 每个表情4字含义标签 |

---

### 【步骤 8】输出交付

返回 `$DIR_PATH` 路径，**告知用户以下内容**：

```
生成完成！产物位于：$DIR_PATH

📦 可直接上传微信的文件在 wechat_export/ 目录：
  - main/           → 240×240 主图（static 为 PNG，animated 为 GIF），按编号命名
  - thumb/          → 120×120 缩略图
  - cover.png       → 专辑封面
  - banner.png      → 详情页横幅
  - icon.png        → 聊天面板图标
  - upload_info.txt → 名称/介绍/版权文案，可直接复制到微信后台

🗂 原始素材：
  static 模式 → 各 static_XX/ 目录下的 origin/（原始切片）和 nobg/（透明背景版）
  animated 模式 → 各 anim_XX/ 目录下的 origin/、nobg/、animated_sticker.gif
```

详细查看和上传步骤见 `reference/output_guide.md`。

---

## 手动流程（无 API Key）

> 适用于未配置 API Key 的情况。用户自己去外部平台出图，Agent 负责 prompt 生成和后处理。

### 手动步骤 0：收集用户需求

> **⛔ 同完整流水线步骤 0。逐项追问，8 项全部收齐并得到用户汇总确认后，才可继续。不得自行填默认值。**

### 手动步骤 1：创建沙盒目录

```bash
DIR_PATH=$(python3 sticker_utils.py create_dir --provider gemini)
echo "沙盒目录：$DIR_PATH"
```

### 手动步骤 2：处理定妆图

| 用户情况           | 操作                                                 |
| ------------------ | ---------------------------------------------------- |
| 提供了定妆图路径   | `cp "<用户路径>" "$DIR_PATH/base_reference.png"`     |
| 在对话中上传了图片 | `cp "<上传图片路径>" "$DIR_PATH/base_reference.png"` |
| 无定妆图           | 跳过本步骤，后续 prompt 会用纯文字描述角色           |

### 手动步骤 3：写入 params.json

注意使用 `<< EOF`（无引号）以展开 `$DIR_PATH` 变量：

```bash
cat > "$DIR_PATH/params.json" << EOF
{
  "mode": "static",
  "set_name": "表情包名称",
  "set_description": "套件描述（不超过80字）",
  "copyright_info": "版权信息",
  "character_name": "角色名称",
  "character_prompt": "角色外观描述（只写外观，不写动作）",
  "reference_image": "$DIR_PATH/base_reference.png",
  "style_preset": "2D_KAWAII",
  "custom_style": "",
  "scene_theme": "COMPREHENSIVE",
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
    {"action": "动作描述1", "text": "配文1"},
    {"action": "动作描述2", "text": "配文2"},
    {"action": "动作描述3", "text": "配文3"},
    {"action": "动作描述4", "text": "配文4"},
    {"action": "动作描述5", "text": "配文5"},
    {"action": "动作描述6", "text": "配文6"},
    {"action": "动作描述7", "text": "配文7"},
    {"action": "动作描述8", "text": "配文8"},
    {"action": "动作描述9", "text": "配文9"}
  ]
}
EOF
```

### 手动步骤 4：生成 Prompt 文件

```bash
python3 sticker_utils.py build_prompts $DIR_PATH
```

**生成后，用 realpath 获取目录的真实绝对路径，并告知用户：**

```bash
realpath "$DIR_PATH"
```

在对话中明确告诉用户：

```
✅ Prompt 已生成，目录位于：
/Users/你的用户名/实际路径/sticker_20260417_120000/

static 模式：各表情 prompt 在 static_01/prompt.txt、static_02/prompt.txt……
animated 模式：各帧 prompt 在 anim_01/prompt.txt、anim_02/prompt.txt……
```

> static 模式依次展示 `static_01`、`static_02`、`static_03`……（按实际生成的数量）
> animated 模式依次展示 `anim_01`、`anim_02`……

### 手动步骤 5：引导用户去外部平台出图

**在对话中告知用户（逐条说清楚）：**

1. **Prompt 已显示在上方**，请直接复制对应编号的 Prompt 文字去外部平台出图
2. **如果有定妆图**，出图时必须同时上传 `$DIR_PATH/base_reference.png` 作为参考图（路径已在上面显示），否则每张图角色外观不一致
3. 建议**逐个处理**，先完成第 1 张，满意后再做下一张，完成后发回给 Agent
4. 详细平台操作（千问/豆包/Gemini）见 `reference/external_platform_guide.md`

**⚠️ 每次只展示一个 Prompt，等用户完成后再给下一个，避免用户混淆。**

### 手动步骤 6：接收用户返回的图片并放入对应目录

用户每发回一张图片，执行（XX 替换为实际编号 01、02、03...）：

```bash
# static 模式
cp "<用户发回的图片路径>" "$DIR_PATH/static_XX/original_grid.png"

# animated 模式
cp "<用户发回的图片路径>" "$DIR_PATH/anim_XX/original_grid.png"
```

全部收齐后（或每收到一张后）继续下一步，已有图片的目录不会被重复处理。

### 手动步骤 7：切片处理

```bash
python3 sticker_utils.py process $DIR_PATH
```

### 手动步骤 8：生成微信物料（必须执行）

```bash
python3 sticker_utils.py wechat_meta $DIR_PATH
```

### 手动步骤 9：输出交付

同完整流水线步骤 8，返回路径并告知用户产物位置。

---

## 附加彩蛋：用户直接提供宫格图（跳过生图步骤）

如果用户已经有一张画好的 9宫格或16宫格图，可以直接处理：

```bash
# 1. 新建沙盒
DIR_PATH=$(python3 sticker_utils.py create_dir --provider gemini)

# 2. 创建子目录并放入宫格图
#    static 模式用 static_01，animated 模式用 anim_01
mkdir -p "$DIR_PATH/anim_01"
cp "<用户提供的宫格图路径>" "$DIR_PATH/anim_01/original_grid.png"

# 3. 直接执行切片（跳过步骤 2-5）
python3 sticker_utils.py process $DIR_PATH

# 4. 生成微信物料（不可跳过）
python3 sticker_utils.py wechat_meta $DIR_PATH
```
