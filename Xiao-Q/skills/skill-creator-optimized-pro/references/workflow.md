# Skill Creator 优化工作流

## 1. 新建 Skill

1. 访谈需求：目标、触发表达、排除条件、输入、输出、完成标准。
2. 判断复杂度：L1/L2/L3/L4。
3. 生成目录结构。
4. 编写 `SKILL.md`，确保 front matter 可解析。
5. 按需生成 `references/`、`scripts/`、`assets/`。
6. 生成 README、测试 Prompt、优化说明。
7. 执行质量门禁并打包。

## 2. 优化既有 Skill

1. 解包或读取现有目录。
2. 读取 `SKILL.md`、README、metadata、references、scripts。
3. 审计：触发、边界、流程、输出契约、引用路径、临时文件。
4. 保留原有有效结构，只修复影响触发、执行、验证和发布的问题。
5. 修复 YAML 并实际解析。
6. 统一版本、名称、README 和 package metadata。
7. 补充方法论、QA 或错误处理 reference。
8. 打包并给出变更说明。

## 3. 验证顺序

1. YAML front matter 解析。
2. JSON/package metadata 解析。
3. 本地引用路径检查。
4. 临时/敏感文件扫描。
5. zip 结构检查。
6. 测试 Prompt 覆盖。

## 4. 汇报格式

- 完成状态。
- 输出文件。
- 修复的问题。
- 验证结果。
- 后续建议。
