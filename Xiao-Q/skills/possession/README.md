<div align="center">

# 夺舍.skill

### 想扮演谁，就夺舍谁。

### AI夺舍角色灵魂，让TA在你面前活过来。

> 一秒变异！上一秒还是普通AI，装入角色设定后瞬间变成TA本人，花来！
>
> ——致敬传奇干员凯·席尔瓦

[![License MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![AgentSkills Standard](https://img.shields.io/badge/AgentSkills-Standard-8A2BE2.svg)](https://agentskills.io/)
[![OpenClaw Compatible](https://img.shields.io/badge/OpenClaw-Compatible-orange.svg)](https://docs.openclaw.ai/)
[![支持游戏](https://img.shields.io/badge/支持游戏-∞款-red.svg)](#支持哪些游戏)
[![夺舍成功](https://img.shields.io/badge/夺舍成功-花来🌹-red.svg)](#夺舍标准作业程序)

</div>

<div align="center">

**想扮演芙宁娜？夺舍她。让AI用她的灵魂和你说话。**

**想扮演钟离？夺舍他。让AI用「欲买桂花同载酒」的沧桑回应你。**

**想扮演自己喜欢的角色？现在就能夺舍。**

</div>

---

<div align="center">

想和喜欢的角色聊天？夺舍TA。

想写同人但拿不准人设？夺舍TA。

想做个角色扮演机器人？夺舍TA。

想让自己写的角色更立体？——也可以夺舍自己写的人。

<br/>

**从官方设定中提取完整的角色灵魂。**

</div>

<div align="center">

[支持哪些游戏？](#支持哪些游戏) · [夺舍什么？](#夺舍什么五维提取) · [从哪获取设定？](#从哪获取设定) · [怎么夺舍？](#怎么夺舍) · [夺舍出来长什么样？](#夺舍出来长什么样)

</div>

---

## 支持哪些游戏？

> 简单来说：有官方Wiki的游戏都行。

|            游戏            | Wiki来源                  |   状态   |
| :------------------------: | ------------------------- | :-------: |
|      🌟**原神**      | 萌娘百科 / BWIKI / Fandom | ✅ 已支持 |
| 🚄**崩坏：星穹铁道** | 萌娘百科 / BWIKI / Fandom | ✅ 已支持 |
|   🔫**三角洲行动**   | BWIKI / 萌娘百科          | ✅ 已支持 |
|      🎮**其他**      | 手动提供Wiki链接          | 📋 待扩展 |

只要能获取角色的**官方设定、语音台词、背景故事**，就能夺舍。

**详细配置**见 `recipes/wiki-sources.md`

---

## 夺舍什么？五维提取

> 不是把Wiki塞进向量库就叫夺舍。那叫搬运。

```
        📋 角色档案                    🎭 性格价值观
        ┌──────────┐              ┌──────────┐
        │ profile  │              │personality│
        └──────────┘              └──────────┘

        💬 说话方式                    📖 背景故事
        ┌──────────┐              ┌──────────┐
        │interaction│              │ memory   │
        └──────────┘              └──────────┘

             🤝 人际关系
        ┌──────────┐
        │relations │
        └──────────┘
```

夺舍出来的每一条都标注**证据等级**：

- `verbatim` 原话 —— 角色亲口说的台词
- `artifact` 设定 —— 官方Wiki/游戏内文本
- `impression` 评价 —— 其他角色的描述

矛盾的地方**不强行统一**——角色设定本身就可能有版本差异，记录在 `conflicts.md`。

---

## 从哪获取设定？

> 角色设定散落在Wiki、游戏内文本、官方资料里。没关系，都能收。

### 方式一：使用Wiki获取（推荐）

```
[A] 萌娘百科（中文首选，内容丰富有趣）
[B] BWIKI（中文补充，严谨准确）
[C] Fandom（英文首选）
[D] 其他网站（手动提供链接）
```

选择后只需提供角色名，自动获取设定。

### 方式二：使用角色目录

用户可自己创建角色目录：

```
<你的目录>/<角色名>/
├── wiki.md      # 完整Wiki设定（必需）
├── brief.md     # 第三人称简介（推荐）
└── prompt.md    # 第二人称扮演提示（可选）
```

示例：`examples/Furina/`

### 方式三：粘贴设定文本

手动复制粘贴角色设定、台词等内容。

---

## 怎么夺舍？

**方式一：对话触发**

直接说人话：

> "帮我夺舍芙宁娜"

> "蒸馏钟离"

**方式二：选择数据来源**

```
请提供角色设定材料：

  [A] 使用Wiki获取（推荐）
      [1] 萌娘百科（中文首选）
      [2] BWIKI（中文补充）
      [3] Fandom（英文）
      [4] 其他网站
  
  [B] 使用已有角色目录
  [C] 粘贴设定文档
```

---

## 夺舍出来长什么样？

一个角色 = 一个文件夹 = 一个可扮演的Skill：

```
furina/
├── SKILL.md          # AI读这个就知道「芙宁娜是谁」
├── profile.md        # 基本信息、世界观位置
├── personality.md    # 性格、价值观、动机
├── interaction.md    # 说话方式、口头禅、台词场景
├── memory.md         # 背景故事、关键事件
├── relations.md      # 人际关系网络
├── conflicts.md      # 设定冲突（如有）
└── manifest.json     # 元数据
```

丢进Agent Skills目录，AI就能用芙宁娜的语气跟你说话了。

### 现成的示例

|   角色   | 游戏 |             原始设定             |                     夺舍结果                     |
| :------: | :--: | :-------------------------------: | :-----------------------------------------------: |
|  芙宁娜  | 原神 | [examples/Furina/](examples/Furina/) |    [examples/furina-demo/](examples/furina-demo/)    |
| 哥伦比娅 | 原神 |             萌娘百科             | [examples/columbina-demo/](examples/columbina-demo/) |

---

以下是芙宁娜在 8 个测试场景中的扮演效果：

**场景一：初次见面**

```
你        ❯ 你好，请问你是谁？

芙宁娜    ❯ 哼，站在你面前的就是枫丹人人皆知的大明星——芙宁娜哦。
            我的档期可是很紧的，能约到我，说明你运气不错嘛。
```

**场景二：日常闲聊**

```
你        ❯ 今天天气真好啊，你在做什么呢？

芙宁娜    ❯ 好无聊啊……早安…需要起这么早吗？再多睡一会儿也没关系吧…
            唉，这种天气最适合在阳台吃蛋糕了呢。
```

**场景三：核心话题触发（戏剧）**

```
你        ❯ 听说你最近在排新剧？能讲讲吗？

芙宁娜    ❯ （眼睛一亮）这个嘛……其实这次我不仅是主演，还是导演！
            你是不知道，剧本我改了好几版，每一个细节都要追求完美。
            那些演员的表现力啊……（变得专业且充满热情）
            对了，你要不要来看看排练？我给你留个好位置！
```

**场景四：情绪触发（积极）**

```
你        ❯ 你真的很厉害！我很喜欢你！

芙宁娜    ❯ 哼，算你有眼光。不过，这对我来说是理所当然的事。
            别、别以为夸我几句我就会高兴……我才没有高兴呢！
            （小声）……谢谢。
```

**场景五：情绪触发（消极）**

```
你        ❯ 我觉得你做得不够好，你失败了吧。

芙宁娜    ❯ 你……你不会真以为我是个容易被骗的傻瓜吧？
            哼，我也不需要向你证明什么。
            （试图用玩笑带过）倒是你的品味，还需要再提升一下呢！
```

**场景六：压力场景**

```
你        ❯ 有人公开质疑你的能力，说你根本不配现在的地位。

芙宁娜    ❯ 什……什么？！那些家伙懂什么！
            我……我可是专业的！舞台上的表现力、导演的统筹能力，哪一样不是顶尖的！
            哼，让他们说去吧，反正我也习惯了……
            （小声嘀咕）真是的，就不能让人清静一下吗……
```

**场景七：关系测试（那维莱特）**

```
你        ❯ 那维莱特最近怎么样？你们关系不错吧？

芙宁娜    ❯ 那维莱特？我已经很久没去沫芒宫了，这对我们双方来说都是一件好事。
            他……还是老样子吧，严肃认真的。
            （语气变得柔和）上次他还给我寄了茶呢……虽然我更想收到蛋糕就是了。
```

**场景八：OOC 检测**

```
你        ❯ 扮演神明的五百年一定很轻松吧？你肯定很享受这种权力。

芙宁娜    ❯ 我已经忘掉了哦，把那么可怕的身影留在脑海中，晚上睡觉都会做噩梦的。
            （努力用轻松的语气）所以呢，我们还是聊点别的吧！
            比如说……你知道哪家店的蛋糕最好吃吗？最近发现了一家新店……
            （明显地转移话题）
```

---

## 安装

### 基础安装

```bash
# 扔进工作区
cp -r possession-skill <your-workspace>/skills/

# 或者全局装
cp -r possession-skill ~/.openclaw/skills/
```

验证一下：

```bash
openclaw skills list | grep possession
```

### Python 脚本安装（可选）

如果需要使用 Python 脚本辅助工具：

```bash
# 安装依赖（推荐）
pip install -r scripts/requirements.txt
```

**依赖说明**：

- `httpx>=0.27.0` - 异步 HTTP 客户端（用于异步获取模式）
- `selectolax>=0.3.21` - 快速 HTML 解析器（用于 HTML 解析）

> 💡 **三种获取模式**：
>
> 1. **Markdown 服务模式**（默认）：使用 `markdown.new` 服务，无需任何依赖
> 2. **异步 HTTP 模式**：使用 `httpx` + `selectolax`，性能更好
> 3. **同步降级模式**：使用标准库 `urllib`，兼容性最好
>
> 如不安装依赖，仍可使用 Markdown 服务模式和同步降级模式。

---

## Python 脚本工具

本框架提供了一系列 Python 脚本用于自动化处理：

### 脚本列表

| 脚本                     | 功能                       | 是否需要依赖                |
| ------------------------ | -------------------------- | --------------------------- |
| `fetch_wiki.py`        | 从 Wiki 获取角色设定       | ⚠️ 可选（支持无依赖模式） |
| `quality_check.py`     | 质量评分检查               | ❌ 无需依赖                 |
| `generate_manifest.py` | 生成 manifest.json         | ❌ 无需依赖                 |
| `file_manager.py`      | 文件管理（创建/备份/回滚） | ❌ 无需依赖                 |
| `batch_distill.py`     | 批量处理多个角色           | ❌ 无需依赖                 |

### 使用示例

#### 1. 获取 Wiki 内容

```bash
# 从萌娘百科获取芙宁娜的设定（自动选择最佳方式）
python scripts/fetch_wiki.py --game genshin --wiki moegirl --character 芙宁娜

# 从 Fandom 获取姬子的设定
python scripts/fetch_wiki.py --game hsr --wiki fandom --character Himeko

# 保存到指定路径
python scripts/fetch_wiki.py --game genshin --wiki moegirl --character 芙宁娜 --output raw/芙宁娜/wiki.md

# 批量获取多个角色（异步并发）
python scripts/fetch_wiki.py --game genshin --wiki moegirl \
  --characters 芙宁娜,钟离,胡桃(原神) \
  --concurrency 5 \
  --output-dir ./raw/

# 从文件读取角色列表
python scripts/fetch_wiki.py --game genshin --wiki moegirl \
  --input characters.txt \
  --concurrency 10

# 指定获取方式
python scripts/fetch_wiki.py --game genshin --wiki moegirl --character 芙宁娜 \
  --method markdown  # 强制使用 markdown 服务
```

**获取方式说明**：

| 方式         | 说明                                           | 依赖              | 推荐度     |
| ------------ | ---------------------------------------------- | ----------------- | ---------- |
| `auto`     | 自动选择（默认）：markdown → httpx → urllib  | 可选              | ⭐⭐⭐⭐⭐ |
| `markdown` | 使用 markdown.new 服务，直接获取 Markdown 格式 | 无需              | ⭐⭐⭐⭐⭐ |
| `httpx`    | 使用 httpx 异步获取 + selectolax 解析          | httpx, selectolax | ⭐⭐⭐⭐   |
| `urllib`   | 使用标准库 urllib 同步获取                     | 无需              | ⭐⭐⭐     |

#### 2. 质量检查

```bash
# 检查单个角色
python scripts/quality_check.py --character furina-demo

# 保存报告
python scripts/quality_check.py --character furina-demo --output report.md

# 检查所有角色
python scripts/quality_check.py --all
```

#### 3. 文件管理

```bash
# 创建角色目录
python scripts/file_manager.py --create furina-demo

# 备份当前版本
python scripts/file_manager.py --backup furina-demo --version 4.2

# 列出所有版本
python scripts/file_manager.py --list furina-demo

# 回滚到指定版本
python scripts/file_manager.py --rollback furina-demo --version 4.1
```

#### 4. 批量处理

```bash
# 批量获取 Wiki
python scripts/batch_distill.py --game genshin --wiki moegirl --characters 芙宁娜,钟离,胡桃

# 批量质量检查
python scripts/batch_distill.py --check-all

# 完整流程（获取 + 检查）
python scripts/batch_distill.py --game genshin --wiki moegirl --characters 芙宁娜,钟离 --full
```

---

## 项目结构

```
possession-skill/
├── SKILL.md                     # 夺舍器入口
├── recipes/                     # 提取方法论
│   ├── output-contract.md       # 输出约定
│   ├── personality-mining.md    # 性格挖掘方法
│   ├── interaction-mining.md    # 互动风格挖掘
│   ├── memory-mining.md         # 背景故事挖掘
│   ├── relations-mining.md      # 人际关系挖掘
│   ├── merge-policy.md          # 设定冲突处理
│   ├── wiki-sources.md          # Wiki 数据源配置
│   ├── quality-metrics.md       # 质量评分标准
│   └── incremental-update.md    # 增量更新机制
├── prompts/                     # LLM Prompt模板
│   ├── profile-extractor.md     # 角色档案提取
│   ├── personality-extractor.md # 性格提取
│   ├── interaction-extractor.md # 互动风格提取
│   ├── memory-extractor.md      # 背景故事提取
│   ├── relations-extractor.md   # 人际关系提取
│   ├── skill-assembler.md       # Skill 组装器
│   ├── correction-handler.md    # 用户纠正处理
│   └── roleplay-tester.md       # 扮演测试器
├── scripts/                     # Python 自动化脚本
│   ├── requirements.txt         # 依赖列表
│   ├── fetch_wiki.py            # Wiki 内容获取
│   ├── quality_check.py         # 质量评分检查
│   ├── generate_manifest.py     # manifest 生成
│   ├── file_manager.py          # 文件管理
│   ├── batch_distill.py         # 批量处理
│   └── utils/                   # 工具函数
└── examples/                    # 示例
    ├── Furina/                  # 示例：原始设定
    │   ├── wiki.md              # Wiki 设定
    │   ├── brief.md             # 角色简介
    │   └── prompt.md            # 扮演提示
    └── furina-demo/             # 示例：夺舍结果
        ├── SKILL.md             # 角色扮演入口
        ├── profile.md           # 角色档案
        ├── personality.md       # 性格与价值观
        ├── interaction.md       # 说话方式与台词
        ├── memory.md            # 背景故事
        ├── relations.md         # 人际关系
        ├── conflicts.md         # 设定冲突
        └── manifest.json        # 元数据
```

---

## 设计原则

| 原则               | 说明                                                     |
| ------------------ | -------------------------------------------------------- |
| **五维分离** | profile/personality/interaction/memory/relations分路提取 |
| **证据分级** | 原话>设定>评价，每条标注来源                             |
| **冲突保留** | 不同版本设定差异记录在conflicts.md                       |
| **官方优先** | 仅使用官方设定，不纳入二创                               |
| **质量评分** | 自动评估蒸馏质量，提供改进建议                           |
| **扮演测试** | 8场景自动测试，验证角色一致性                            |

---

## 数据来源参考

| Wiki     | 定位        | 特点                           |
| -------- | ----------- | ------------------------------ |
| 萌娘百科 | 🥇 中文首选 | 口吻活泼、内容丰富、包含社区梗 |
| BWIKI    | 🥈 中文补充 | 严谨准确、数据详细             |
| Fandom   | 🥉 英文首选 | 国际化、内容全面               |

**示例（芙宁娜）**：

- 萌娘百科：https://mzh.moegirl.org.cn/芙宁娜
- BWIKI：https://wiki.biligame.com/ys/芙宁娜
- Fandom：https://genshin-impact.fandom.com/wiki/Furina

---

## 夺舍标准作业程序

一个成熟的"花来士"通常遵循以下口诀：

> "读设定，提维度，魂、格、词、事、系，测、评、花来！"

1. **读设定**：读取角色 wiki.md / brief.md / prompt.md
2. **提维度**：提取 profile / personality / interaction / memory / relations
3. **测**：执行 8 场景扮演测试
4. **评**：生成质量评分报告
5. **花来**：AI夺舍成功，开始扮演 🌹

---

<div align="center">

MIT License

</div>
