# Sprite Editor + Tile Palette

---

## Sprite Editor（精灵编辑器）

**打开方式：** 在 Project 窗口选中图片 → Inspector 中 Texture Type 设为 `Sprite (2D and UI)` → Sprite Mode 设为 `Multiple` → 点击 **Sprite Editor** 按钮

---

### 进入条件
- **Texture Type** 必须设置为 `Sprite (2D and UI)`
- **Sprite Mode** 必须设置为 `Multiple`（单张图切多 Sprite）
- 下方才出现 **Sprite Editor** 按钮

---

### 窗口工具栏

| 按钮 | 功能 |
|------|------|
| **Slice** | 打开切片面板——自动/手动切分 Sprite |
| **Apply** | 保存修改 |
| **Revert** | 撤销未应用的修改 |
| **Alpha/RGB 切换** | 查看 Alpha 通道或完整 RGB 图像 |
| **Mipmap 滑块** | 切换纹理 Mipmap 级别预览 |

---

### 自动切片（Slice 面板）

点击 **Slice** 按钮打开：

#### Type（切片方式）

| 类型 | 说明 |
|------|------|
| **Automatic** | 基于**透明边界**自动检测每个 Sprite 区域。适合每个图之间有透明间隔的 Sprite Sheet |
| **Grid By Cell Size** | 按固定**像素尺寸**等大切片（设置 Pixel Size 的宽高） |
| **Grid By Cell Count** | 按固定**行列数**等分切片（设置 Column & Row） |
| **Isometric Grid** | 等距/2.5D 菱形切片（半高菱形） |

#### 通用属性

| 属性 | 说明 |
|------|------|
| **Offset** | 网格从左上角偏移（X, Y 像素） |
| **Padding** | Sprite 间距（Grid 类型用） |
| **Keep Empty Rects** | 保留无像素的空 Sprite（非 Automatic 类型） |
| **Pivot** | 预设轴心位置：Center / Top-Left / Top / Top-Right / Left / Right / Bottom-Left / Bottom / Bottom-Right / Custom |
| **Pivot Unit Mode** | Normalized（0-1）/ Pixels（绝对像素） |
| **Custom Pivot** | Pivot 设为 Custom 时自定义 X/Y 值 |
| **Slice on Import** | 文件更新时自动重新切片 |

#### Method（冲突处理——切片时已存在 Sprite 的处理）

| 方法 | 说明 |
|------|------|
| **Delete Existing** | 删除所有现有 SpriteRect，替换为新切片 |
| **Smart** | 新 SpriteRect 与旧的重叠时更新旧的，丢弃新的 |
| **Safe** | 保留所有旧 SpriteRect，丢弃与旧重叠的新切片 |

---

### 切片后编辑

切片完成后，可单击每个 SpriteRect（包围框）：
- 调整边框大小（拖拽边界）
- 重命名（右侧面板）
- 调整 Pivot（拖拽轴心点）
- 查看尺寸和位置信息

---

### 九宫格切片（9-Slicing）

1. 切换到 Sprite Editor 窗口
2. 拖拽绿色边框控制点（L, R, T, B）定义拉伸/固定区域
3. 中间区域可拉伸，四个角保持原大小
4. 适用于 UI 背景、按钮等

---

### 切片操作流程（十步法）

1. 选中 Sprite Sheet 图片
2. Inspector 中 Texture Type → Sprite (2D and UI)，Sprite Mode → Multiple
3. 点击 **Sprite Editor**
4. 点击 **Slice**
5. 选择 Type（如 Grid By Cell Size）
6. 输入像素尺寸
7. 设置 Pivot
8. 选择方法（首次选 Delete Existing）
9. 点击 Slice 按钮
10. 点击 **Apply** 保存

---

## Tile Palette（瓦片调色板）

**打开方式：** `Window > 2D > Tile Palette`

用于在 Tilemap 上绘制瓦片。

### 使用步骤

1. `Window > 2D > Tile Palette` 打开面板
2. 创建一个 Tilemap：Hierarchy 右键 → `2D Object > Tilemap > Rectangular`（或 Hexagonal/Isometric）
3. 拖拽 Sprite 图片到 Tile Palette 面板 → 选择保存位置 → 创建 Tile 资源
4. 选择画笔工具（面板顶部）
5. 在 Scene 视图中点击 Tilemap 网格绘制

### 顶部工具栏

| 工具 | 功能 |
|------|------|
| 画笔（Brush） | 在 Tilemap 上绘制选中的 Tile |
| 矩形框选 | 框选区域批量绘制 |
| 吸管（Picker） | 从 Tilemap 中吸取已有的 Tile |
| 橡皮擦（Eraser） | 擦除 Tile |
| 填充（Fill） | 区域填充同一种 Tile |
| 旋转/翻转 | 旋转或镜像 Tile 方向 |

### 编辑模式（Edit 按钮）

点击后进入编辑模式，可调整已绘制 Tile 的属性（位置、旋转等）。

---

## Tilemap Renderer

Tilemap GameObject 自带 Tilemap Renderer 组件，与 Sprite Renderer 类似，按 Sorting Layer/Order 与其他 2D 内容共同排序。
