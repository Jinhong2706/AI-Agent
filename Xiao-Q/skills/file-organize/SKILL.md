---
name: file-organizer
description: 整理文件夹中的文件，按类型分类到对应子文件夹中。支持按扩展名（文档、图片、视频、压缩包、安装程序、代码等）自动分类，也可自定义规则。当用户提到"整理文件"、"分类文件"、"组织文件夹"、"清理下载"、"file organizer"、"organize"等词语时使用此skill。
---

# File Organizer

整理指定文件夹中的文件，按类型自动分类到子文件夹中。

## 分类规则

| 类别 | 子文件夹名 | 扩展名 |
|------|-----------|--------|
| 文档 | 文档 | .pdf, .docx, .doc, .md, .txt, .pptx, .ppt, .xlsx, .xls |
| 图片 | 图片 | .png, .jpg, .jpeg, .gif, .bmp, .svg, .webp, .ico |
| 压缩包 | 压缩包 | .zip, .rar, .7z, .tar, .gz, .mrpack |
| 安装程序 | 安装程序 | .exe, .msi, .msu |
| DLL文件 | DLL文件 | .dll |
| 代码 | 代码 | .java, .py, .js, .ts, .html, .css, .json, .xml, .yaml, .yml, .c, .cpp, .h, .go, .rs |
| 日志 | 日志 | .log |
| Minecraft | Minecraft | .litematic, .schematic |
| 其他 | 其他 | 以上未覆盖的扩展名 |

## 工作流程

1. 扫描目标文件夹中的所有文件（不处理已有子文件夹）
2. 按扩展名匹配分类规则
3. 创建分类子文件夹（如果不存在）
4. 移动文件到对应子文件夹
5. 输出整理报告

## 注意事项

- 不要移动已有的子文件夹
- 如果目标子文件夹中已有同名文件，在文件名后添加数字后缀避免覆盖
- 汇总整理结果报告给用户
