# 屏幕录制静止片段剪辑助手

[English](./README.en.md)

`screen-idle-video-cutter` 是一个面向屏幕录制的低 token 视频剪辑 Skill。它用本地脚本识别长时间没有动作的静止画面，并在删除片段前后各保留 5 秒，方便后续拼接和检查。

## 当前版本

- 版本：`1.0.0`
- 更新日期：`2026-05-22`
- Skill 文件：[SKILL.md](./SKILL.md)
- 发布信息：[PUBLISH_INFO.md](./PUBLISH_INFO.md)
- 更新记录：[CHANGELOG.md](./CHANGELOG.md)

## 解决什么问题

很多屏幕录制视频里会有长时间无操作的停顿，比如等待加载、思考、复制资料、切换窗口前后的空白。手动找这些片段很慢，把视频帧交给模型看又会消耗大量 token。

这个 Skill 的策略是：

- 用 `ffmpeg` 低频抽帧
- 用 `Pillow` 和 `numpy` 比较相邻帧差异
- 本地判断静止区间
- 删除静止区间中间部分
- 每个删除区间前后默认保留 `5` 秒

## 默认行为

- 静止阈值：连续 `15` 秒低画面变化
- 保护空挡：删除片段前后各 `5` 秒
- 抽样频率：`1 fps`
- 输出：剪辑后视频、JSON 报告、可选 segment 文件
- 原则：宁可少删，也不要误删有动作画面

## 快速使用

```bash
cd skills/screen-idle-video-cutter
python3 scripts/screen_idle_cutter.py input.mp4 --output output.mp4 --report report.json --segments segments.txt
```

重要视频建议先预览：

```bash
python3 scripts/screen_idle_cutter.py input.mp4 --output output.mp4 --dry-run --report report.json --segments segments.txt
```

## 常用参数

- `--min-static-seconds 15`：连续多少秒静止才认为可剪。
- `--guard-seconds 5`：删除片段前后保留多少秒。
- `--sample-fps 1`：每秒抽多少帧用于检测。
- `--diff-threshold auto`：自动估计静止差异阈值，也可传入数字。
- `--dry-run`：只生成报告和剪辑清单，不渲染视频。
- `--report report.json`：输出可审计 JSON 报告。
- `--segments segments.txt`：输出 ffmpeg concat 片段文件。

## 包内容

```text
screen-idle-video-cutter/
├── SKILL.md
├── README.md
├── README.en.md
├── CHANGELOG.md
├── PUBLISH_INFO.md
├── .skillignore
├── scripts/
│   ├── screen_idle_cutter.py
│   ├── validate_skill.py
│   ├── package_skill.py
│   └── validate_release_package.py
└── tests/
    └── test_segment_math.py
```

## 当前 MVP 取舍

这个版本有意不包含 `references/`、`templates/`、`examples/`。

原因是：

- 核心能力已经收敛到一个可直接运行的本地脚本
- 目标是先把低 token 静止检测和裁剪流程做成可发布最小闭环
- 后续如果需要扩展多套参数模板、样例工程或高级说明，再补充这些目录

## 验证与打包

```bash
python3 scripts/validate_skill.py
python3 tests/test_segment_math.py
python3 scripts/package_skill.py
python3 scripts/package_skillhub.py
python3 scripts/validate_release_package.py dist/screen-idle-video-cutter.skill
python3 scripts/validate_release_package.py dist/screen-idle-video-cutter.zip
```

## 发布说明

主上传文件：

```text
dist/publish/screen-idle-video-cutter-skillhub-v1.0.0.zip
```

备用上传文件：

```text
dist/screen-idle-video-cutter.skill
```

不要上传仓库根目录，也不要上传 GitHub 自动生成的源码压缩包。
