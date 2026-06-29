# Lighting 窗口 + Quality Settings + Graphics Settings

---

## Lighting 窗口

**打开方式：** `Window > Rendering > Lighting`

管理场景的全局光照（GI）、环境光和光照烘焙设置。

### 三个标签页
- **Scene** — 场景光照全局配置
- **Realtime Lightmaps**（Built-in RP） — 实时全局光照贴图
- **Baked Lightmaps** — 烘焙后的光照贴图预览

所有配置存储在一个 **Lighting Settings Asset** 中。

---

### Scene 标签页

#### Environment（环境光）

| 属性 | 说明 |
|------|------|
| **Skybox Material** | 天空盒材质。默认为内置 Default Skybox。可替换为自定义天空盒 |
| **Sun Source** | 指定一个 Directional Light 作为太阳。设为 None 时自动选最亮的 Directional Light |

**Environment Lighting（环境光照）：**

| 属性 | 说明 |
|------|------|
| **Source** | Skybox（从天空盒取色，最精确）/ Gradient（天空-地平线-地面渐变）/ Color（纯色） |
| **Intensity Multiplier** | 环境光亮度（0-8，默认 1） |

**Environment Reflections（环境反射）：**

| 属性 | 说明 |
|------|------|
| **Source** | Skybox / Custom（自定义 Cubemap） |
| **Resolution** | 反射 Cubemap 分辨率 |
| **Compression** | Auto / Uncompressed / Compressed |
| **Intensity Multiplier** | 反射可见程度 |
| **Bounces** | 反射弹跳次数（默认 1） |

#### Mixed Lighting（混合光照）

| 属性 | 说明 |
|------|------|
| **Baked Global Illumination** | **启用**以使用烘焙 GI 系统。关闭时所有 Baked/Mixed 灯光表现为 Realtime |
| **Lighting Mode** | Baked Indirect（实时直接光+烘焙间接光）/ Shadowmask（实时直接光+烘焙间接+混合阴影）/ Subtractive（静态物体烘焙直/间接光，动态物体仅实时直光） |
| **Realtime Shadow Color** | Subtractive 模式下实时阴影的颜色 |

#### Lightmapping Settings（烘焙参数）

| 属性 | 说明 |
|------|------|
| **Lightmapper** | Progressive CPU / Progressive GPU（预览）/ Enlighten（2022.3 已弃用隐藏） |
| **Lightmap Resolution** | 每单位 Texel 数。越大越精细但**成倍**增加烘焙时间。测试用 5-10，最终用 20-80 |
| **Lightmap Padding** | UV 岛间距（Texel）。默认 2 |
| **Max Lightmap Size** | 单张 Lightmap 最大尺寸（像素）。默认 1024，高质量用 4096 |
| **Lightmap Compression** | None / Low / Normal / High。看到斑驳阴影时设为 None |
| **Ambient Occlusion** | 烘焙 AO。启用后设 Max Distance（射线距离）、Indirect/Direct Contribution |
| **Directional Mode** | Directional（生成第二张 Lightmap 存主光方向，法线贴图可接受烘焙光）≈2x VRAM / Non-directional（单张，省内存） |
| **Indirect Intensity** | 间接光亮度倍数 |
| **Albedo Boost** | 反照率增强（1-10）。1 为物理准确 |
| **Lightmap Parameters** | 预设质量控制：Default-Medium / HighResolution / LowResolution / VeryLowResolution |

#### 工作流控制（窗口底部）

| 按钮 | 功能 |
|------|------|
| **Auto Generate** | 场景变化后自动重新烘焙（编辑时不建议开启） |
| **Generate Lighting** | 手动触发全量烘焙。下拉选项：Bake Reflection Probes / Clear Baked Data |

---

### 烘焙快速检查清单

1. `Window > Rendering > Lighting` → 确保 **Baked GI** 启用
2. 标记静态物体为 **Static**（至少勾选 Contribute GI）
3. 灯光 Mode 设为 **Baked** 或 **Mixed**
4. 场景中放置 **Light Probes**（给动态物体接收间接光）
5. 点击 **Generate Lighting** 开始烘焙

---

## Quality Settings（画质设置）

**路径：** `Edit > Project Settings > Quality`

### 画质等级
6 个预设等级（Very Low 到 Ultra），可增删。每个等级配置：

| 属性 | 说明 |
|------|------|
| **Pixel Light Count** | 逐像素光照最大数量 |
| **Texture Quality** | Full Res / Half Res / Quarter Res / Eighth Res |
| **Anisotropic Textures** | 各向异性过滤 |
| **Anti Aliasing** | Disabled / 2x / 4x / 8x MSAA |
| **Soft Particles** | 软粒子开关 |
| **Shadows** | Hard and Soft / Hard Only / Disable |
| **Shadow Resolution** | Low / Medium / High / Very High |
| **Shadow Distance** | 阴影可见距离 |
| **VSync Count** | Every V Blank / Every Second V Blank / Don't Sync |
| **LOD Bias** | LOD 切换距离阈值 |
| **Maximum LOD Level** | 最高 LOD 级别 |

### 平台默认
- 每个平台分别设置默认使用哪个画质等级
- 点击平台图标右侧下拉选择

---

## Graphics Settings（图形设置）

**路径：** `Edit > Project Settings > Graphics`

| 设置 | 说明 |
|------|------|
| **Scriptable Render Pipeline Settings** | URP / HDRP 管线资源引用 |
| **Tier Settings** | 渲染层级（Low/Medium/High）设置 |
| **Always Included Shaders** | 构建时始终包含的 Shader（不依赖引用扫描） |
| **Preloaded Shaders** | 启动时预加载的 Shader |
| **Shader Stripping** | Shader 变体剔除（减小构建体积） |
| **Fog** | 全局雾效模式设置 |
| **Camera Settings** | 默认摄像机设置 |
