# SD场景描写指南

## 核心原则

**每句文案 → 每帧画面 → 每张SD图**
不是一整段配一张图，而是**每句核心画面**都配一张图。

---

## SD提示词结构（通用模板）

```
【正向提示词】
(1girl/1boy/2girls), 主体外貌描述, 具体动作, 表情, 服装细节, 场景背景, 光线描述, 视角, 画质标签

【负向提示词】
lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry

【参数】
Steps: 25-30
Sampler: DPM++ 2M Karras
CFG scale: 7-8
Size: 768x1024（竖版）或 1024x768（横版）
```

---

## 古风场景快速词库

### 人物主体

```
# 男性
古风美男, 黑发束冠, 剑眉星目, 身姿挺拔, 战甲/铠甲/长袍, 佩剑/长矛, 站姿/坐姿/策马
三国武将, 燕颔虎须（张飞特征）, 面如冠玉（赵云特征）, 帝王之气

# 女性
古风美女, 黑发如瀑/双髻, 鹅蛋脸, 柳叶眉, 杏眼含泪, 肤若凝脂, 华服/素衣
丫鬟发髻, 身披斗篷, 低头含羞, 眼神哀伤, 身怀六甲（卞雪特征）

# 群像
多人, 古风, 士兵阵列, 铠甲, 武器, 军旗飘扬
```

### 场景背景

```
军营大帐, 帅帐内, 案桌, 烛火, 军事地图, 沙盘
城楼之上, 城墙, 远山, 战旗, 烽火台
荒野山坡, 杂草丛生, 孤坟, 天空阴霾
洛阳城门, 城门楼, 石板路, 百姓围观
行军途中, 官道, 骑兵, 步兵, 尘土飞扬
```

### 光线与氛围

```
黄昏光线, 夕阳西下, 金色余晖
月光皎洁, 夜色深沉, 星空
烛火摇曳, 暖光, 帐内昏暗
战火硝烟, 冷色调, 压迫感
清晨薄雾, 朦胧感, 湿润空气
```

### 视角

```
正面全身像：full body, front view
侧面特写：side profile, close-up face
背面/远景：back view, distant shot
俯视全景：aerial view, wide shot
仰视（显威严）：low angle, looking up
```

---

## 古风分类场景模板

### 三国军营场景

```
# 场景1：军营大帐议事
主体：1boy, 古风男性, 铠甲, 坐于帅案后, 神情严肃, 手持竹简
背景：军营大帐, 案桌, 烛火摇曳, 地图挂墙, 帐外夜色
光线：烛光暖黄, 帐内明暗对比
视角：正面中景
正向：1boy, Chinese general, armor, sitting behind a military desk, serious expression, candlelight, military tent interior, night scene, warm lighting, detailed, high quality
负向：lowres, bad anatomy, bad hands, text, error, missing fingers, worst quality, low quality

# 场景2：校场点兵
主体：古风将领站在高台, 身后军旗飘扬, 下方士兵阵列整齐
背景：宽阔校场, 战鼓, 军旗, 铠甲反射日光
光线：正午日光, 硬光, 气势磅礴
视角：侧面全景
正向：Chinese general standing on platform, soldiers in formation, military drums, flags, daytime, dramatic lighting, cinematic composition, high quality
负向：lowres, bad anatomy, worst quality, low quality
```

### 古风人物情感场景

```
# 场景3：握手暧昧
主体：1girl and 1boy, 古风, 男子牵着少女的手, 少女低头含羞, 面色绯红
背景：军营帐帘, 营帐内景, 简洁
光线：自然光透帐, 柔和
视角：侧面中景，手部特写
正向：1girl and 1boy, Chinese ancient style, young woman blushing, lowering head shyly, young man holding her hand gently, military tent background, soft natural lighting, intimate atmosphere, detailed hands, high quality
负向：lowres, bad anatomy, bad hands, worst quality, low quality

# 场景4：孤坟告别
主体：古风少女跪于孤坟前, 神情悲伤, 泪眼婆娑, 双手抚碑
背景：荒野, 杂草丛生, 天空阴霾, 孤坟石碑, 远处枯树
光线：阴天, 冷色调, 低沉氛围
视角：侧面近景
正向：1girl, Chinese ancient style, mourning at grave, tearful eyes, hands on tombstone, wilderness background, cloudy sky, cold tones, melancholic atmosphere, detailed, high quality
负向：lowres, bad anatomy, bad hands, worst quality, low quality
```

### 战争与攻城场景

```
# 场景5：10万大军压境
主体：远景, 襄平城城墙, 城外黑压压的骑兵步兵阵列, 军旗如林
背景：襄平城, 城墙, 护城河, 敌军大营帐篷密密麻麻
光线：黄昏, 暗色调, 压迫感
视角：俯视全景
尺寸：1024x768（横版）
正向：ancient Chinese city walls, massive enemy army in background, cavalry and infantry formation, hundreds of military tents, war banners, dusk, dark atmosphere, cinematic, dramatic, bird eye view, high quality
负向：lowres, worst quality, low quality, blurry

# 场景6：夜袭烧粮
主体：骑兵小队, 夜色中, 点燃火箭, 向敌营冲去, 火光映照
背景：敌营, 粮草堆, 火焰, 混乱, 夜空中火光冲天
光线：火光, 橙红色调, 明暗对比强烈
视角：正面全景
尺寸：1024x768
正向：night raid, cavalry小队 with flaming arrows, charging into enemy camp, fire burning, flames in night sky, dramatic lighting, orange and red tones, cinematic scene, high quality
负向：lowres, bad anatomy, worst quality, low quality
```

---

## 现代都市场景

```
# 场景7：都市总裁
主体：1boy, 现代男性, 西装革履, 站立于落地窗前, 俯瞰城市夜景, 自信神情
背景：现代都市, 城市夜景, 霓虹灯光, 玻璃幕墙
光线：城市灯光, 冷暖对比
视角：侧面/背面
正向：1boy, modern young man, business suit, standing by floor-to-ceiling window, overlooking city night view, confident expression, modern office, city lights, cinematic lighting, high quality
负向：lowres, bad anatomy, bad hands, worst quality, low quality

# 场景8：电话催债
主体：1boy, 现代男性, 手持手机, 表情淡漠/冷笑, 周围办公环境
背景：豪华办公室, 落地窗, 城市背景, 办公桌
光线：日光, 明亮, 冷色调
视角：正面中景
正向：1boy, modern Chinese man, holding smartphone, cold expression, casual clothes, luxury office background, city view through window, natural daylight, high quality
负向：lowres, bad anatomy, bad hands, worst quality, low quality
```

---

## 改写时自动生成场景的原则

1. **列出文案中所有核心画面**（每一句口播内容，对应一个视觉场景）
2. **判断场景类型**（古风/现代/玄幻/都市）
3. **提取关键视觉元素**（人物、动作、服装、环境）
4. **匹配光线与氛围**（配合文字情绪）
5. **生成标准SD提示词**（遵循上述模板结构）

### 示例：从文案自动提取场景

文案：
```
「她问我愿不愿意带她走，我沉默了」
```
→ 提取视觉元素：两人、古风、室外、情绪场景
→ 选择场景模板：古风情感场景
→ 输出SD提示词
