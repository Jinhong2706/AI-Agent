# 能力清单

本文件记录 ADP 多模态能力的已核实事实，只保留模块、模式、参数、结果结构和调用链信息。

## 模块映射

| 模块 | 模型 | 别名 | 对应能力 |
|---|---|---|---|
| `image` | `hy` | `image.hy` | 图片生成（3.0） |
| `image` | `gi` | `image.gi` | 图片生成 GI 版 |
| `video` | `kling` | `video.kling` | 可灵视频生成 |
| `video` | `vidu` | `video.vidu` | VIDU 视频生成 |
| `3d` | `hy` | `3d.hy` | 混元生 3D（专业版） |

## 统一执行方式

所有能力都按异步任务执行：

1. 调用 submit 工具
2. 从 submit 成功结果中提取 `JobId`
3. 调用配套的 query 工具
4. 轮询直到任务完成
5. 从 query 结果中提取最终资源

统一脚本入口：

```bash
python3 scripts/adp_mcp.py <alias> run [--mode <mode>] [--step <submit|query>] '<json>'
```

使用约定：

- 默认方式是直接执行完整链路，不带 `--step`
- 只有在默认全流程执行拿不到结果，或需要排查 submit / query 某个具体阶段时，才使用 `--step`
- `--step submit` 用于只执行提交任务
- `--step query` 用于拿已有 `JobId` 单独查询结果

## image.hy

- 别名：`image.hy`
- 支持模式：
  - `text2image`
  - `image2image`
- 工具链：
  - submit：`SubmitTextToImageJob`
  - query：`QueryTextToImageJob`
- submit 参数：
  - `Prompt`：必填，图片描述
  - `Resolution`：选填，目标分辨率
  - `Images`：选填，图生图参考图 URL 列表
  - `Revise`：选填，是否启用 prompt 改写
  - `Seed`：选填，随机种子
  - `LogoAdd`：选填，是否添加水印
  - `LogoParam`：选填，水印内容配置
- 模式约束：
  - `text2image`：至少提供 `Prompt`
  - `image2image`：必须同时提供 `Prompt + Images`
- query 参数：
  - `JobId`：必填
- query 成功字段：
  - `JobStatusCode`
  - `JobStatusMsg`
  - `JobErrorCode`
  - `JobErrorMsg`
  - `ResultImage[]`
  - `ResultDetails[]`
  - `RevisedPrompt[]`
  - `RequestId`
- 最终资源：
  - `ResultImage[]`：图片 URL 列表
- 成功样例结构：
  - submit：
    - `JobId = "<job-id>"`
    - `RequestId = "<request-id>"`
  - query：
    - `JobStatusCode = "5"`
    - `JobStatusMsg = "处理完成"`
    - `JobErrorCode = ""`
    - `JobErrorMsg = ""`
    - `ResultImage = ["<image-url>"]`
    - `ResultDetails = ["Success"]`
    - `RevisedPrompt = ["<revised-prompt>"]`
    - `RequestId = "<request-id>"`

## image.gi

- 别名：`image.gi`
- 支持模式：
  - `text2image`
  - `image2image`
- 工具链：
  - submit：`SubmitGIImageJob`
  - query：`QueryGIImageJob`
- submit 参数：
  - `Prompt`：必填，图片描述
  - `AspectRatio`：选填，画面比例
  - `Images`：选填，参考图数组
  - `Images[].Base64`：选填，参考图 base64
  - `Images[].Url`：选填，参考图 URL
  - `Resolution`：选填，目标分辨率
- 模式约束：
  - `text2image`：至少提供 `Prompt`
  - `image2image`：必须同时提供 `Prompt + Images`
- query 参数：
  - `JobId`：必填
- query 成功字段：
  - `Status`
  - `ErrorCode`
  - `ErrorMessage`
  - `ResultImages[]`
- 最终资源：
  - `ResultImages[]`：图片 URL 列表
- 成功样例结构：
  - submit：
    - `JobId = "<job-id>"`
  - query：
    - `Status = "DONE"`
    - `ErrorCode = ""`
    - `ErrorMessage = ""`
    - `ResultImages = ["<image-url>"]`

## video.kling

- 别名：`video.kling`
- 支持模式：
  - `text2video`
  - `image2video`
- 文生视频工具链：
  - submit：`SubmitKlingTextToVideoJob`
  - query：`QueryKlingTextToVideoJob`
- 文生视频 submit 参数：
  - `Prompt`
  - `NegativePrompt`
  - `AspectRatio`
  - `CfgScale`
  - `Duration`
  - `Model`
- 文生视频 query 参数：
  - `JobId`
- 文生视频 query 成功字段：
  - `Status`
  - `ErrorCode`
  - `ErrorMessage`
  - `ResultVideoUrl`
- 文生视频成功样例结构：
  - submit：
    - `JobId = "<job-id>"`
  - query：
    - `Status = "DONE"`
    - `ErrorCode = ""`
    - `ErrorMessage = ""`
    - `ResultVideoUrl = "<video-url>"`
- 图生视频工具链：
  - submit：`SubmitKlingImageToVideoJob`
  - query：`QueryKlingImageToVideoJob`
- 图生视频 submit 参数：
  - `Image.Base64` 或 `Image.Url`
  - `Prompt`
  - `NegativePrompt`
  - `CfgScale`
  - `Duration`
  - `Model`
- 图生视频 query 参数：
  - `JobId`
- 图生视频 query 成功字段：
  - `Status`
  - `ErrorCode`
  - `ErrorMessage`
  - `ResultVideoUrl`
- 图生视频成功样例结构：
  - submit：
    - `JobId = "<job-id>"`
  - query：
    - `Status = "DONE"`
    - `ErrorCode = ""`
    - `ErrorMessage = ""`
    - `ResultVideoUrl = "<video-url>"`

## video.vidu

- 别名：`video.vidu`
- 支持模式：
  - `text2video`
  - `image2video`
- 文生视频工具链：
  - submit：`SubmitViduTextToVideoJob`
  - query：`QueryViduTextToVideoJob`
- 文生视频 submit 参数：
  - `Prompt`
  - `AspectRatio`
  - `Bgm`
  - `Duration`
  - `Resolution`
- 文生视频 query 参数：
  - `JobId`
- 文生视频 query 成功字段：
  - `Status`
  - `ErrorCode`
  - `ErrorMessage`
  - `ResultVideoUrl`
- 文生视频成功样例结构：
  - submit：
    - `JobId = "<job-id>"`
  - query：
    - `Status = "DONE"`
    - `ErrorCode = ""`
    - `ErrorMessage = ""`
    - `ResultVideoUrl = "<video-url>"`
- 图生视频工具链：
  - submit：`SubmitViduImageToVideoJob`
  - query：`QueryViduImageToVideoJob`
- 图生视频 submit 参数：
  - `Images`
  - `Prompt`
  - `Audio`
  - `Duration`
  - `Resolution`
  - `VoiceId`
- 图生视频 query 参数：
  - `JobId`
- 图生视频 query 成功字段：
  - `Status`
  - `ErrorCode`
  - `ErrorMessage`
  - `ResultVideoUrl`
- 图生视频成功样例结构：
  - submit：
    - `JobId = "<job-id>"`
  - query：
    - `Status = "DONE"`
    - `ErrorCode = ""`
    - `ErrorMessage = ""`
    - `ResultVideoUrl = "<video-url>"`

## 3d.hy

- 别名：`3d.hy`
- 支持模式：
  - `text23d`
  - `image23d`
- 工具链：
  - submit：`SubmitHunyuanTo3DProJob`
  - query：`QueryHunyuanTo3DProJob`
- submit 参数：
  - `Prompt`
  - `ImageBase64`
  - `ImageUrl`
  - `MultiViewImages`
  - `GenerateType`
  - `PolygonType`
  - `FaceCount`
  - `EnablePBR`
- 模式约束：
  - `text23d`：至少提供 `Prompt`
  - `image23d`：至少提供 `ImageBase64` 或 `ImageUrl`
- query 参数：
  - `JobId`
- query 成功字段：
  - `Response.Status`
  - `Response.ResultFile3Ds[]`
  - `Response.ResultFile3Ds[].Type`
  - `Response.ResultFile3Ds[].Url`
  - `Response.ResultFile3Ds[].PreviewImageUrl`
  - `Response.RequestId`
- 最终资源：
  - `Response.ResultFile3Ds[]`
  - 典型返回包含预览图、`zip` 和 `glb`
- 成功样例结构：
  - submit：
    - `Response.JobId = "<job-id>"`
    - `Response.RequestId = "<request-id>"`
  - query：
    - `Response.Status = "DONE"`
    - `Response.ResultFile3Ds = [{"Type":"OBJ","Url":"<zip-url>","PreviewImageUrl":"<preview-image-url>"},{"Type":"GLB","Url":"<glb-url>","PreviewImageUrl":"<preview-image-url>"}]`
    - `Response.RequestId = "<request-id>"`
