# 风险参考库

> **代码索引式查表**：STEP 5 对每一帧，依据该帧 STEP 3 已确定的【镜头码（情绪 A–G / 类型叠加 H）+ 镜头语言/构图/表演特征】，在下方各库的【触发条件】列命中对应行，注入其关键词。**不再靠语义自由联想匹配。**
>
> 命中流程：
> ```
> 每帧 → 取 STEP3 设计：情绪码 / 类型叠加码 / 运镜 / 构图特征 / 表演动作 / 道具 / 环境
>      → 扫【触发条件】列：标"全局"的所有帧必注；其余按特征/码命中即注
>      → 生图风险注入【风险约束】(A库)；视频风险注入视频【风险约束】(B库)
> 整段成套场景 → 直接套用 C 库对应组合包
> ```

---

## A. 生图逐帧风险库（手绘草稿 + 木偶小人构图专用）

> 本库专为多宫格分镜故事板的手绘草稿/木偶小人画风设计。
> 木偶小人具备简化身体结构（头部、颈、躯干、上臂/前臂、大腿/小腿、简化手掌/脚掌及各关节），无五官、发型、服装。
> 所有条目均围绕草稿质感一致性、木偶小人跨帧稳定性、构图结构准确性展开。

| 触发条件（按帧 STEP3 设计判定） | 画面内容特征 | 典型风险 | 注入关键词 |
|------------|------------|---------|-----------|
| **全局**（每帧必注） | 所有帧画风 | 部分帧画风写实化漂移，偏离手绘铅笔草稿质感；或精细程度突变 | `all panels strictly maintain rough pencil sketch quality, no panel-to-panel rendering variation, no realistic facial or body surface detail` |
| **全局**（每帧必注） | 帧内标注文字 | 标注缺失、位置偏移至格内、格式不符（应在格上方单行） | `every panel must display annotation label above the frame in exact format: index number, shot abbreviation, pipe, core content` |
| **全局**（有角色帧） | 木偶小人体型 | 头部/躯干/四肢各段比例跨帧突变，或整体身高相对场景比例失真 | `maintain consistent puppet figure body segment proportions and overall scale across all panels` |
| **全局**（有角色帧） | 木偶关节角度 | 关节角度（肩/肘/腕/髋/膝/踝）无动作依据突变，或姿势与剧本动作不符 | `preserve physically motivated joint angles across panels, no unmotivated limb rotation or joint snapping` |
| **全局**（有角色帧） | 木偶关节连接点 | 身体段连接点断裂、空隙或消失，肢体"悬浮脱离"躯干 | `all body segments must connect at joint points without gaps or floating disconnection` |
| **全局**（有角色帧） | 简化手掌/脚掌 | 手掌/脚掌向写实手指/趾偏移，或跨帧大小突变 | `maintain simplified block-shape hands and feet, no realistic finger or toe detail, consistent hand-foot scale across all panels` |
| 构图含 ≥2 角色 | 多个木偶同框 | 体型相近难分身份，或AI将两人合并 | `clearly separate puppet A and puppet B by spatial position and pose gesture, no figure merging or overlap confusion` |
| 表演含道具交互（握/用/推拉） | 道具与木偶交互 | 道具悬浮于手掌末端无接触，或尺寸相对木偶失真 | `prop visually contacts puppet hand endpoint, prop size proportional to puppet body scale` |
| 帧含道具（@道具） | 道具放置位置 | 道具跨帧移位、消失或方向突变 | `preserve exact prop placement, orientation and relative position to characters across all panels` |
| 构图含前景遮挡 | 前景遮挡物（门框/柱/树干/窗框） | 前景线条元素跨帧消失或位移，破坏构图一致 | `maintain foreground sketch elements in consistent position and form across all panels` |
| 同场景跨景别（远↔近帧） | 背景场景结构 | 同场景背景草图在远景与特写帧结构对不上，或元素随机替换 | `preserve identical background structural sketch lines between wide and close shots, no background element substitution` |
| 场景有透视空间（走廊/室内/街景） | 场景透视 | 透视消失点跨帧漂移，透视基准不一致 | `maintain consistent perspective vanishing point and line guide across all panels` |
| 构图为对称（常见于 A2/E3） | 对称构图（宫门/长廊/门洞） | 对称线条与透视轴跨帧偏移或扭曲 | `maintain strict structural symmetry and perspective axis consistent across all panels` |
| 环境含雨/雾/烟/尘 | 大气效果（线条/纹理笔触） | 各帧大气线条方向、密度或分布跳变 | `consistent atmospheric line direction and stroke density throughout all panels` |
| **全局**（每帧必注） | 网格分隔线 | 分隔线粗细不均、断裂、或与内容重叠 | `uniform separator line weight between panels, clean grid boundaries, no line overlap with panel content` |
| **全局**（每帧必注） | 线条笔触质感 | 部分帧线条变印刷体/矢量感，失手绘质感；或粗细差异过大 | `consistent hand-drawn pencil line weight and texture across all panels, avoid mechanical or vector-style lines` |
| 表演含持械 / **H1·H3** | 木偶持械（刀/棍/枪械） | 武器与手掌接触点断裂、尺寸失真、跨帧形态变化 | `weapon prop contacts puppet hand grip point, consistent weapon size proportional to puppet, preserve identical weapon form across all panels` |
| 帧含车辆 / **H4** | 车辆作为大型道具 | 车辆相对木偶/场景比例失真、跨帧车型变化、车轮接触地面漂浮 | `maintain vehicle scale proportional to puppet figures and scene, preserve identical vehicle structure across all panels, wheels contact ground without floating` |
| 运镜快速或挥击 / **H1·H2·H4** | 速度/动作线条 | 动势线条方向混乱、跨帧密度跳变、掩盖木偶主体动作 | `consistent motion line direction following the action vector, uniform stroke density across panels, motion lines support not obscure the puppet pose` |
| 帧含开火/爆炸 / **H2·H3** | 火光/枪口闪光/爆炸（笔触表现） | 闪光/爆炸线条随机突变、位置脱离枪口/爆点 | `muzzle flash and explosion rendered as consistent radial sketch strokes anchored to weapon barrel or blast origin` |

---

## B. 视频逐段风险库

| 触发条件（按帧镜头语言+表演判定） | 动作/镜头特征 | 典型风险 | 注入关键词 |
|-------------|------------|---------|-----------|
| 表演含起身/坐下 | 人物起身/坐下 | 重心变化不自然、动作漂浮 | `realistic weight shift and center of gravity change, grounded body mechanics` |
| 表演含转身/回头 | 角色转身/回头 | 转身过程面孔变形或替换 | `preserve facial identity through full rotation, no face morph during turn` |
| 运镜=推/拉（Dolly） | 慢推/慢拉镜头 | 镜头运动变成平面2D缩放 | `genuine dolly/push motion with perspective change, not flat 2D zoom` |
| 运镜=手持 | 手持镜头 | AI输出完全稳定的机械运动 | `subtle handheld camera shake, organic micro-vibration throughout` |
| 运镜=跟拍 | 斯坦尼康/跟拍 | 稳定过头失去跟拍感 | `steadicam smoothness with slight lag and organic weight, not robotic stabilization` |
| 运镜=环绕 | 环绕镜头（360°） | 环绕过程中背景错位 | `maintain spatial consistency during circular camera movement, no background discontinuity` |
| 运镜=升/降（Crane） | 升降镜头 | 高度变化时透视不连续 | `smooth perspective transition during vertical camera movement, continuous architectural lines` |
| 表演含道具拿放 | 道具拿起/放下 | 道具与手部穿插/悬浮 | `physically accurate hand-prop contact, no floating or clipping` |
| 角色有长发/飘动衣物+风或运动 | 布料/头发飘动 | 飘动违反物理（逆重力/无惯性） | `fabric and hair motion follows realistic physics and wind direction` |
| 有面部情绪表演 | 面部情绪微变化 | AI过度夸张或面孔替换 | `subtle emotional transition, micro muscle movement, preserve character face` |
| 帧含台词 | 人物对话 | 嘴型与台词节奏不符 | `lip movement naturally matches dialogue rhythm, no exaggerated mouth animation` |
| 光影含渐变（烛光/日落） | 环境光渐变 | 光影瞬间跳变 | `gradual and continuous light transition, no sudden lighting jump cut` |
| 相邻帧景别跳变（远↔特写） | 跨帧景别切换 | 切换时黑帧或跳切 | `smooth visual transition between shots, maintain spatial continuity` |
| 环境含水/火/烟 | 水面/火焰/烟雾 | 运动循环感明显或完全静止 | `non-repeating natural motion of water/fire/smoke, organic variation` |
| 表演含打斗/奔跑 / **H1·H2** | 高速动作 | 动作糊成一团或关键帧丢失 | `preserve key action poses, motion blur only on fast-moving limbs not on face` |
| 角色有长发/披风+运动 | 长发/披风运动中 | 头发/披风穿入身体或漂浮异常 | `hair and cape follow body movement with correct physics, no clipping through body` |
| 表演含行走穿越 | 角色行走 | 步伐与地面接触不真实 | `realistic foot contact with ground, natural stride rhythm and weight transfer` |
| 表演含多角色接触 / **H1·H2** | 多角色互动（握手/拥抱/对打） | 身体部位相互穿插 | `physically accurate body contact, no limb intersection or clipping between characters` |
| 场景=走廊/密室+有运镜 | 狭小空间 | 镜头运动时墙壁/边界穿透 | `maintain spatial boundaries, camera movement respects physical walls and obstacles` |
| 帧含文字/符文/印章 | 文字/符文出现 | AI随机生成错误文字 | `if text elements appear, maintain exact character form with no improvised alterations` |
| **H1·H2** | 武打招式连贯性 | 招式糊成一团、关键招式帧丢失、方位混乱看不清谁打谁 | `preserve key martial arts poses with clear spatial orientation, motion blur only on striking limbs, maintain who-hits-whom readability` |
| **H1**（持械打斗） | 武器挥砍/格挡接触 | 武器与身体/兵器接触点穿插、或无接触却产生火花 | `physically accurate weapon contact point on impact, no clipping through body, impact spark anchored to actual contact` |
| **H3** | 枪口闪光与后坐力 | 开火无闪光/无后坐、或闪光与射击节奏脱节 | `synchronized muzzle flash with recoil kick on each shot, flash timing matches firing rhythm` |
| **H3** | 弹壳抛出/弹匣更换 | 弹壳数量或轨迹不合理、换弹动作漂浮无重量 | `realistic shell ejection trajectory and count, grounded reload motion with weight, no floating parts` |
| **H4** | 高速车辆运动 | 车辆呈2D平移、缺前景视差、速度感缺失 | `genuine vehicle motion with foreground parallax and motion blur conveying real speed, not flat 2D translation` |
| **H2·H4** | 爆炸/撞击冲击波 | 冲击波瞬间静止或循环感、碎片违反物理 | `non-repeating explosion shockwave with physically motivated debris trajectory, no frozen or looping blast` |

---

## C. 高频组合场景速查（按镜头码直接套用）

> 整段属于以下成套场景时，直接套用对应组合包（A + B 库组合），无需逐行命中。

### 室内对话场景（草图 · A3/B2/G1）
**生图重点**：多个木偶同框 + 家具道具位置 + 室内透视基准  
**视频重点**：面部情绪微变化 + 环境光渐变 + 对话嘴型  
**推荐注入**：
```
clearly separate puppet A and puppet B by position and pose, no figure merging,
preserve exact furniture placement across all panels,
maintain consistent interior perspective vanishing point,
subtle emotional transition with micro muscle movement,
gradual light transition without sudden jump, lip movement matches dialogue rhythm
```

### 动作/追逐场景（草图 · 通用，更具体见 H1–H4）
**生图重点**：木偶体型跨帧一致性 + 关节角度合理性 + 道具接触  
**视频重点**：高速动作关键帧 + 多角色互动 + 手持抖动  
**推荐注入**：
```
maintain consistent puppet body segment proportions across all panels,
preserve physically motivated joint angles, no unmotivated limb rotation,
prop visually contacts puppet hand endpoint,
preserve key action poses with motion blur only on fast-moving limbs,
physically accurate body contact during action sequences,
subtle handheld camera shake with organic micro-vibration
```

### 空镜/风景场景（草图 · G2/G4）
**生图重点**：大气效果线条一致性 + 背景透视基准  
**视频重点**：大气流动 + 光线渐变  
**推荐注入**：
```
consistent atmospheric line direction and stroke density throughout all panels,
maintain consistent perspective vanishing point across all panels,
non-repeating natural motion of environmental elements,
gradual and continuous light transition throughout
```

### 多镜多道具场景（草图 · G4/道具密集）
**生图重点**：道具放置位置 + 前景遮挡物 + 木偶关节连接  
**视频重点**：道具拿起/放下 + 角色行走  
**推荐注入**：
```
preserve exact prop placement, orientation and relative position across all panels,
maintain foreground sketch elements consistent in position and form,
all body segments connect at joint points without gaps or floating disconnection,
physically accurate hand-prop contact, no floating or clipping,
realistic foot contact with ground and natural stride rhythm
```

### 功夫片/武打场景（草图 · H1/H2）
**生图重点**：木偶持械接触 + 体型/关节跨帧一致 + 速度动作线条  
**视频重点**：武打招式连贯性 + 武器挥砍接触 + 手持抖动  
**推荐注入**：
```
weapon prop contacts puppet hand grip point, consistent weapon size proportional to puppet,
maintain consistent puppet body segment proportions and physically motivated joint angles,
consistent motion line direction following the action vector,
preserve key martial arts poses with clear spatial orientation, motion blur only on striking limbs,
physically accurate weapon contact point on impact, no clipping through body,
subtle handheld camera shake with organic micro-vibration
```

### 枪战场景（草图 · H3）
**生图重点**：木偶持枪械接触 + 枪口闪光线条 + 掩体前景遮挡  
**视频重点**：枪口闪光与后坐力 + 弹壳抛出 + 跨帧景别切换  
**推荐注入**：
```
weapon prop contacts puppet hand grip point, preserve identical weapon form across all panels,
muzzle flash rendered as consistent radial sketch strokes anchored to weapon barrel,
maintain foreground cover elements consistent in position and form,
synchronized muzzle flash with recoil kick, flash timing matches firing rhythm,
realistic shell ejection trajectory, smooth visual transition between shots
```

### 飙车场景（草图 · H4）
**生图重点**：车辆大型道具比例 + 速度动作线条 + 场景透视基准  
**视频重点**：高速车辆视差 + 车载/手持抖动 + 环境光频闪  
**推荐注入**：
```
maintain vehicle scale proportional to scene, preserve identical vehicle structure across all panels,
consistent motion line direction following the action vector,
maintain consistent perspective vanishing point across all panels,
genuine vehicle motion with foreground parallax and motion blur conveying real speed,
subtle handheld/mounted camera shake, gradual continuous light transition without sudden jump
```
