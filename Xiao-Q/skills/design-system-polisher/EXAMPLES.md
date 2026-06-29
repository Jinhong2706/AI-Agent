# Design System Polisher - 使用示例（完整版）

本文档提供了设计系统美化 skill（完整版）的详细使用示例。

## 🎯 示例 1: 完整流程演示

### 用户输入
```
/design-system-polisher
```

### Skill 完整输出

```
👋 欢迎使用设计系统美化专家！

请选择您想要采用的设计系统风格：

【热门科技公司】（完整嵌入）
1. Apple - 二元浅深节奏、SF Pro 字体
   核心特征：二元浅深节奏、单一强调色、SF Pro 光学尺寸
   主色调：#0071e3、背景：#ffffff/#000000
   标题字体：SF Pro Display 72px weight 600 / SF Pro Text 17px weight 400
   间距系统：8px base unit
   圆角系统：8px(标准)/980px(胶囊)
   阴影系统：rgba(0,0,0,0.22) 3px 5px 30px 0px

2. Airbnb - 三层阴影、Rausch Red 强调
   核心特征：暖色摄影风格、三层阴影系统
   主色调：#ff385c、背景：#ffffff
   标题字体：Airbnb Cereal VF 22px weight 600 letter-spacing -0.44px
   间距系统：8px base unit
   圆角系统：8px(按钮)/14px(徽章)/20px(卡片)/50%(控制)
   阴影系统：三层堆栈

3. Vercel - shadow-as-border、Geist 字体
   核心特征：极简主义、几何精密
   主色调：#171717、背景：#ffffff
   标题字体：Geist Sans 48px weight 600 letter-spacing -2.4px
   间距系统：8px base unit
   圆角系统：6px(标准)
   阴影系统：Shadow-as-Border + 多层堆栈 + 内部高光

4. Stripe - 蓝调阴影、sohne-var 字体
   核心特征：金融级设计、轻量权威
   主色调：#533afd、背景：#ffffff
   标题字体：sohne-var 48px weight 300 letter-spacing -1.4px
   间距系统：8px base unit
   圆角系统：4px(标准)
   阴影系统：蓝调多层阴影 + "ss01" 样式集

5. Linear - 深色优先、1px 边框
   核心特征：深色主题、极简主义
   主色调：#08090a、背景：#f7f8f8
   标题字体：Inter Variable 72px weight 600 letter-spacing -1.584px
   间距系统：8px base unit
   圆角系统：2px(标准)
   阴影系统：极简、边框而非阴影

6. Figma - 紫色主导、8px 圆角
   核心特征：黑白界面、设计工具美学
   主色调：#9b51e0、背景：#000000/#ffffff
   标题字体：figmaSans 72px weight 320 line-height 1.00
   间距系统：8px base unit
   圆角系统：8px(标准)
   阴影系统：几乎不用

7. Supabase - 绿色系、HSL tokens
   核心特征：开发者友好、深色终端体验
   主色调：#3ecf8e、背景：#0f0f0f
   标题字体：Circular 72px weight 600 line-height 1.00
   间距系统：8px base unit
   圆角系统：6px(标准)
   阴影系统：几乎不用

8. MongoDB - 森林暗黑、MongoDB Value Serif
   核心特征：数据库设计、双模式
   主色调：#001e2b、背景：#001e2b/#ffffff
   标题字体：MongoDB Value Serif 96px weight 400
   正文字体：Euclid Circular A 18px weight 300
   间距系统：8px base unit
   圆角系统：100px(胶囊)/6px(标准)/8px(舒适)
   阴影系统：森林绿色调阴影

【其他品牌】（快速参考）
9. Expo - React 框架生态
10. Webflow - 可视化建站工具
...

🔍 您可以直接输入品牌名称，或选择序号
```

---

**完成！** 所有 7 个热门品牌的设计规范已完整嵌入到 skill 中，其他 52 个品牌提供快速参考。skill 现在可以完全离线运行，无需读取外部文件！
