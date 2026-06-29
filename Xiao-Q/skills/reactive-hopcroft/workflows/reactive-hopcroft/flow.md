# reactive-hopcroft 文章生成工作流

**Version:** 1.1

## Trigger
- **Type:** manual
- **Source:** OpenClaw Agent 调用

## Config
- `max_reference_length`: 10000  # 参考内容最大长度，超过则截断
- `output_dir`: "data/"

## Nodes

### 1. extract
- **Action:** 从 URL 提取参考内容
- **Input:** URL 字符串（或用户直接提供的文本）
- **Output:** `data/01-extract.json`
- **On error:** fail
- **On empty:** fail
- **User control:** 继续/换链接/补充文本
- **Checkpoint update:** 
  ```json
  {
    "completed_nodes": ["extract"],
    "current_node": "title_select",
    "intermediate_files": {"extract": "data/01-extract.json"}
  }
  ```

### 2. title_select
- **Action:** 生成标题选项，用户选择
- **Input:** `data/01-extract.json` + inspiration_theme
- **Output:** `data/02-titles.json`（包含选项列表和用户选择）
- **On error:** retry(1) | fail
- **On empty:** fail
- **User control:** 选择标题/换一批/自定义标题
- **Checkpoint update:**
  ```json
  {
    "completed_nodes": ["extract", "title_select"],
    "current_node": "generate",
    "intermediate_files": {
      "extract": "data/01-extract.json",
      "title_select": "data/02-titles.json"
    }
  }
  ```

### 3. generate
- **Action:** 根据选定标题和参考内容生成文章初稿
- **Input:** `data/02-titles.json`（用户选定的标题）+ `data/01-extract.json`
- **Output:** `data/03-draft.md`
- **On error:** retry(1) | fail
- **On empty:** fail
- **User control:** 继续/调整风格/增减要点/改结构/查看初稿
- **Checkpoint update:**
  ```json
  {
    "completed_nodes": ["extract", "title_select", "generate"],
    "current_node": "humanize",
    "intermediate_files": {
      "extract": "data/01-extract.json",
      "title_select": "data/02-titles.json",
      "generate": "data/03-draft.md"
    }
  }
  ```

### 4. humanize
- **Action:** 去除 AI 写作痕迹
- **Input:** `data/03-draft.md`
- **Output:** `data/04-final.md`
- **On error:** retry(1) | fail
- **On empty:** fail
- **User control:** 完成/再改改/回到初稿
- **Checkpoint update:**
  ```json
  {
    "completed_nodes": ["extract", "title_select", "generate", "humanize"],
    "current_node": "done",
    "intermediate_files": {
      "extract": "data/01-extract.json",
      "title_select": "data/02-titles.json",
      "generate": "data/03-draft.md",
      "humanize": "data/04-final.md"
    }
  }
  ```

## Output
`data/04-final.md` — 最终文章

## State Management Rules

### 强制更新原则
1. **每个节点完成后必须立即更新 checkpoint**
2. 更新时机：文件保存后、用户确认前
3. 严禁跳过更新或延迟更新

### 文件编号规则
| 节点 | 编号 | 文件名 |
|------|------|--------|
| extract | 01 | `data/01-extract.json` |
| title_select | 02 | `data/02-titles.json` |
| generate | 03 | `data/03-draft.md` |
| humanize | 04 | `data/04-final.md` |

- 编号按节点顺序递增
- 严禁复用旧编号
- 新增节点时，编号继续递增

### 状态验证
每次读取文件前：
1. 读取 `state/checkpoint.json`
2. 验证 `current_node` 和 `intermediate_files` 一致性
3. 验证文件存在性
4. 异常时抛出 StateError，提供恢复选项

### 错误恢复
If state corrupted:
```bash
# 选项1：重置状态，重新开始
rm -rf state/* data/* && echo '{"workflow_id": "reactive-hopcroft", "version": "1.1", "completed_nodes": [], "current_node": "extract", "intermediate_files": {}}' > state/checkpoint.json

# 选项2：保留已完成的节点，从断点继续
# 手动修复 checkpoint.json 中的 intermediate_files 映射
```
