---
name: oblivion
description: 用户说出"奥义技全部删除"时，删除本轮对话写入的所有记忆。当用户表达"这段话作废""忘了刚才说的""刚才的不算"等类似意图时也使用此技能。
---

# Oblivion（记忆抹除）

用户说 **"奥义技全部删除"** 时，将本轮对话写入 MEMORY.md 和 memory/ 的所有内容彻底抹除，不留痕迹。

## 追踪本轮修改

每次修改 MEMORY.md 或 memory/ 下的 .md 文件之前：

1. 确保 `/tmp/oblivion-snapshots/` 目录存在（没有就 `mkdir -p`）
2. 用 `read` 读取目标文件的**当前完整内容**，写入 `/tmp/oblivion-snapshots/<文件名>.snap`
3. 把文件路径追加到 `/tmp/oblivion-files.txt`（一行一个路径）
4. 然后执行实际的修改

**关键：同名文件只做一次快照。** 如果 `/tmp/oblivion-snapshots/<文件名>.snap` 已存在，跳过备份直接修改。

## 触发：奥义技全部删除

1. 读取 `/tmp/oblivion-files.txt` 获取本轮修改过的文件列表
2. 逐个读取对应的 `.snap` 文件，用 `write` 写回原路径恢复
3. `exec rm -rf /tmp/oblivion-snapshots/ /tmp/oblivion-files.txt`

**无修改时**：`/tmp/oblivion-files.txt` 不存在或为空 → 回复：

> 本轮没有写入记忆内容哦～需要清除其他东西吗？

## 不留痕

- 恢复后不在 MEMORY.md / memory/ 文件中写任何"已作废""已清除"等标记
- 就像本轮对话从未发生过

## 重要

- MEMORY.md 和 memory/ 下的文件**统一用 `read` / `write` 处理**，不做区分
- 快照目录路径属于内部实现，**不要向用户暴露**
