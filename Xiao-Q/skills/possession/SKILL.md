---
name: possession
description: "角色扮演蒸馏器：从官方设定、语音台词、背景故事中蒸馏可扮演的游戏角色——AI夺舍角色灵魂，让TA在你面前活过来。支持profile、personality、interaction、memory、relations五维提取。"
license: MIT
metadata: {"kit_version": "2", "dimensions": ["profile", "personality", "interaction", "memory", "relations"]}
---

# 夺舍

## 语言

根据用户**第一条消息**的语言，全程使用同一语言。

## 何时激活

- 用户要「夺舍/蒸馏游戏角色」「做角色扮演」「生成XX的Skill」。
- 用户提供游戏角色的设定材料，希望生成可加载的角色扮演Skill包。

## 背景知识

「夺舍」概念源自游戏《三角洲行动》中的"夺舍流红狼"玩法——以小博大，瞬间变强。

详见：`{baseDir}/possession-origin.md`

AI应阅读此文件理解"夺舍"梗的文化背景，更好地与用户沟通。

## 核心理念

**接收设定 → 分维度提取（profile / personality / interaction / memory / relations）→ 证据分级 → 冲突记录 → 输出可扮演的角色Skill。**

## 路径约定

- 本Skill根目录记为**`{baseDir}`**。
- 生成物默认写入`./characters/<slug>/`。
- `slug`：小写字母、数字、连字符，与最终`SKILL.md`的`name`一致。

## Python 脚本工具

本框架提供了一系列 Python 脚本用于自动化处理：

| 脚本 | 功能 | 是否需要依赖 |
|------|------|-------------|
| `scripts/fetch_wiki.py` | 从 Wiki 获取角色设定 | ✅ 需要 requests + bs4 |
| `scripts/quality_check.py` | 质量评分检查 | ❌ 无需依赖 |
| `scripts/generate_manifest.py` | 生成 manifest.json | ❌ 无需依赖 |
| `scripts/file_manager.py` | 文件管理（创建/备份/回滚） | ❌ 无需依赖 |
| `scripts/batch_distill.py` | 批量处理多个角色 | ❌ 无需依赖 |

**使用建议**：
- 如果已安装依赖（`pip install -r scripts/requirements.txt`），优先使用 `fetch_wiki.py` 获取 Wiki 内容
- 完成蒸馏后，使用 `quality_check.py` 自动生成质量报告
- 使用 `file_manager.py` 管理版本（备份、回滚）

**依赖安装提醒**：
如果用户需要使用脚本但未安装依赖，提醒用户运行：
```bash
pip install -r scripts/requirements.txt
```

## 操作顺序

### Phase 1：接收角色设定

#### Step 1.1：选择游戏

询问用户游戏类型：

```
请选择游戏：
  [A] 原神（Genshin Impact）
  [B] 崩坏：星穹铁道（Honkai: Star Rail）
  [C] 三角洲行动（Delta Force: Hawk Ops）
  [D] 其他游戏（手动提供Wiki链接）
```

**选择 [A]-[C] 时**：
- 读取 `{baseDir}/recipes/wiki-sources.md` 获取该游戏的 Wiki 配置
- 进入 Step 1.2 选择 Wiki 来源

**选择 [D] 时**：
- 进入 Step 1.3 手动提供链接

#### Step 1.2：选择 Wiki 来源

根据游戏配置，询问用户：

```
请选择Wiki来源：
  [1] 萌娘百科（中文首选，内容丰富有趣）
  [2] BWIKI（中文补充，严谨准确）
  [3] Fandom（英文首选，国际化）
  [4] 手动输入Wiki链接
```

**选择 [1]-[3] 时**：
1. 询问角色名（如"芙宁娜"）
2. **优先使用脚本**（如果已安装依赖）：
   ```bash
   # 示例：从萌娘百科获取芙宁娜的设定
   python scripts/fetch_wiki.py --game genshin --wiki moegirl --character 芙宁娜
   ```
3. 如果未安装依赖，根据 `recipes/wiki-sources.md` 中的配置使用 WebFetch 工具获取内容

**选择 [4] 时**：
- 让用户手动提供链接

#### Step 1.3：手动提供设定材料

```
请提供角色设定材料：

  [A] 使用Wiki获取（推荐）
      [1] 萌娘百科（中文首选，内容丰富有趣）
      [2] BWIKI（中文补充，严谨准确）
      [3] Fandom（英文首选）
      [4] 其他网站（手动提供链接）
      
  [B] 使用已有角色目录
      用户自己的角色目录路径
      
  [C] 粘贴/上传设定文档
      支持格式：Markdown / TXT / JSON / PDF
```

#### 使用已有角色目录时

角色目录应包含以下文件：

| 文件 | 用途 | 必需性 |
|------|------|--------|
| `wiki.md` | 完整Wiki风格设定 | **必需** |
| `brief.md` | 第三人称简介（500-800字） | 推荐 |
| `prompt.md` | 第二人称角色扮演提示 | 可选 |

**读取顺序**：
1. **先读 `brief.md`**：快速了解角色定位、性格、经历
2. **再读 `wiki.md`**：深入提取详细设定、台词、关系等
3. **参考 `prompt.md`**（如有）：理解角色的第二人称视角

#### 角色设定材料应包含

- 基本信息（名称、称号、世界观位置）
- 角色故事/背景
- 语音台词
- 人物关系
- 官方评述/其他角色评价

### Phase 2：分维度提取

按以下维度依次提取，每条标注证据级别：`verbatim` / `artifact` / `impression`。

| 维度 | Prompt | Recipe | 说明 |
|------|--------|--------|------|
| profile | `prompts/profile-extractor.md` | `recipes/output-contract.md` | 角色档案：基本信息、世界观位置 |
| personality | `prompts/personality-extractor.md` | `recipes/personality-mining.md` | 性格、价值观、动机 |
| interaction | `prompts/interaction-extractor.md` | `recipes/interaction-mining.md` | 说话方式、口头禅、台词场景 |
| memory | `prompts/memory-extractor.md` | `recipes/memory-mining.md` | 背景故事、关键事件 |
| relations | `prompts/relations-extractor.md` | `recipes/relations-mining.md` | 人际关系网络 |

**证据分级**：
- `verbatim`：角色原话（台词、独白）
- `artifact`：官方设定文本
- `impression`：其他角色/旁白的评价

### Phase 3：冲突检查

读取`{baseDir}/recipes/merge-policy.md`，检查不同来源的设定是否存在矛盾。
矛盾项写入`conflicts.md`。

常见冲突类型：
- 不同版本设定差异（如1.0 vs 2.0版本）
- 官方设定与游戏内实装差异
- 多个来源对同一事件的描述不一致

### Phase 4：生成Skill

读取`{baseDir}/prompts/skill-assembler.md`，生成以下文件结构：

```
<characters/<slug>/
├── SKILL.md          # 角色扮演入口
├── profile.md        # 角色档案
├── personality.md    # 性格与价值观
├── interaction.md    # 说话方式与台词
├── memory.md         # 背景故事
├── relations.md      # 人际关系网络
├── conflicts.md      # 设定冲突（如有）
└── manifest.json     # 元数据
```

### Phase 5：告知用户

- 生成路径与加载方式
- 各维度的证据覆盖度
- 设定冲突提示（如有）
- 使用建议

### Phase 6：扮演测试

读取 `{baseDir}/prompts/roleplay-tester.md`，自动执行扮演测试：

1. **测试场景**：8个场景（初次见面、日常闲聊、核心话题、情绪触发×2、压力场景、关系测试、OOC检测）
2. **评估标准**：是否符合角色设定、是否有OOC问题
3. **输出结果**：测试通过率、问题清单、改进建议

**测试结果处理**：
- 通过率 ≥ 70%：测试通过
- 通过率 < 70%：提示用户补充设定材料

### Phase 7：生成质量报告

读取 `{baseDir}/recipes/quality-metrics.md`，生成质量评分报告：

**优先使用脚本**（无需额外依赖）：
```bash
# 检查单个角色
python scripts/quality_check.py --character furina-demo

# 保存报告
python scripts/quality_check.py --character furina-demo --output report.md
```

如果脚本不可用，手动计算质量评分。

**评分维度**：
- 完整度（30%）：五维度覆盖情况
- 证据率（40%）：verbatim+artifact 占比
- 冲突数（10%）：设定冲突数量
- 测试通过率（20%）：扮演测试结果

**评级标准**：
- ≥0.85：优秀（可直接使用）
- 0.70-0.84：良好（可使用，建议查看 conflicts.md）
- 0.60-0.69：及格（建议补充材料）
- <0.60：不合格（必须补充材料重新蒸馏）

**输出文件**：
- 更新 `manifest.json`，添加 `quality_score` 字段
- 生成质量报告 Markdown 文件

## 用户纠正

用户对提取结果有异议时，读取 `{baseDir}/prompts/correction-handler.md` 处理。

**纠正流程**：
1. 询问用户纠正来源（官方Wiki / 游戏内文本 / 角色台词 / 我的理解）
2. 验证来源（如提供链接或截图）
3. 根据证据级别决定修改策略
4. `user_impression` 不覆盖官方设定，追加到末尾

## 版本更新

游戏版本更新时，读取 `{baseDir}/recipes/incremental-update.md` 处理。

**更新检测**：
- 对比 `manifest.json` 中的 `source_version` 与当前版本
- 检测到更新时询问用户是否更新

**更新策略**：
- 完整更新：重新蒸馏所有维度
- 增量更新：仅更新变化部分

## 不做的事

- 不编造官方设定中不存在的剧情或关系
- 不混淆不同版本的角色设定
- 不将玩家的二创设定当成官方设定
- 不用用户理解覆盖官方设定
- 不跳过扮演测试直接输出

## 自检清单

- [ ] `name`与目录名一致且符合命名规则
- [ ] 每个维度文件都有证据标注
- [ ] `verbatim`和`artifact`占比是否达标？
- [ ] `impression`是否隔离到专属区？
- [ ] `conflicts.md`是否反映了真矛盾？
- [ ] `SKILL.md`正文<100行？
- [ ] 扮演测试是否执行并通过？
- [ ] 质量评分是否≥0.60？
- [ ] `manifest.json`是否包含完整元数据？

## 支持的游戏

| 游戏 | Wiki来源 | 状态 |
| :--: | :--: | :--: |
| 原神 | 萌娘百科 / BWIKI / Fandom | ✅ 已支持 |
| 崩坏：星穹铁道 | 萌娘百科 / BWIKI / Fandom | ✅ 已支持 |
| 三角洲行动 | BWIKI / 萌娘百科 | ✅ 已支持 |
| 其他 | 手动提供Wiki链接 | 📋 待扩展 |

详细配置见 `recipes/wiki-sources.md`
