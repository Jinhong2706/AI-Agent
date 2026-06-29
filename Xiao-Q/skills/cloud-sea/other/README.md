# other/ — 非官方峰云海预测

本文件夹存放**非官方16峰**的云海预测配置和脚本。

## 文件说明

| 文件 | 用途 |
|------|------|
| `peaks.json` | 6座非官方峰配置（茶山、喜鹊梁、麻田岭、白谷查山、冰山梁、东猴顶） |
| `forecast.py` | 6峰专用预测脚本（独立运行，不依赖主系统） |

## 使用方法

### 一键预测一周云海概率

```bash
cd C:\Users\86139\.qclaw\skills\cloud-sea\other
python forecast.py
```

输出：
- 概率矩阵表（6峰 × 7天）
- 逐日逐峰详细分析
- 一周推荐总结
- 各峰最佳日

### 自定义日期范围

编辑 `forecast.py` 第296行：
```python
dates = [(today + datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
```
修改 `range(7)` 为 `range(14)` 可预测两周。

## 6峰坐标来源

| 峰名 | 坐标来源 | 海拔来源 |
|------|--------|--------|
| 茶山 | 高德API | 用户提供2524m |
| 喜鹊梁 | 高德API | 用户提供2078m |
| 麻田岭 | 高德API | 用户提供2122m |
| 白谷查山 | 高德API | 用户提供2190m |
| 冰山梁 | 高德API | 用户提供2211m |
| 东猴顶 | 高德API | 用户提供2292.6m |

**注意**：高德API返回的是山脚/居民点坐标，与山顶坐标有偏差。但Open-Meteo API的0.25°网格精度（~25km）下，这个偏差影响不大。

## 与主系统的区别

| 特性 | 主系统（16峰） | other（6峰） |
|------|---------------|--------------|
| 数据来源 | ECMWF IFS + CMA + ENS | ECMWF IFS 0.25° |
| 12因子模型 | 完整 | 简化版 |
| LCL融合 | V2.0三层融合 | 单层LCL |
| 输出格式 | Markdown + HTML + PNG | Markdown终端输出 |
| 配置文件 | `references/peaks.json` | `other/peaks.json` |

## 扩展新峰

1. 在高德API获取坐标：
   ```
   https://restapi.amap.com/v3/geocode/geo?key=YOUR_KEY&address=峰名&city=张家口
   ```

2. 在 `peaks.json` 添加峰信息

3. 重新运行 `forecast.py`

## 已知限制

- ECMWF模型5天后精度递减
- 高德坐标可能偏离山顶（~1-5km）
- 简化12因子模型精度低于主系统
- 无ENS Layer 3仲裁，极端天气下误差增大

## 更新记录

- **2026-05-27**：创建文件夹，添加6峰配置和预测脚本
- **2026-05-27**：高德API获取5座缺失坐标（茶山、喜鹊梁、白谷查山、冰山梁、东猴顶）
