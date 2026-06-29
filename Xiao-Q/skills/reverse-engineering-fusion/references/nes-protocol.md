# 通义灵码 NES 协议完整参考

## 协议概述

NES（Next Edit Suggestion）是通义灵码的代码补全协议，通过 XML 格式描述代码编辑操作。

## 协议格式

```xml
<actions>
  <next_edit>
    <next_file>相对路径或空（空表示当前文件）</next_file>
    <next_start_line>起始行号（1-based）</next_start_line>
    <next_end_line>结束行号（1-based）</next_end_line>
    <next_content>替换内容（CDATA或XML转义）</next_content>
  </next_edit>
</actions>
```

## 语义规则

| startLine | endLine | content | 操作 |
|-----------|---------|---------|------|
| N | N | 非空 | **插入**：在第N行后插入新内容 |
| N | M (N≠M) | 空 | **删除**：删除第N到M行 |
| N | M (N≠M) | 非空 | **替换**：用新内容替换第N到M行 |

## 字段说明

### next_file

- 类型：字符串
- 含义：目标文件相对路径
- 特殊值：空字符串表示当前文件
- 示例：`src/utils/helper.ts` 或 `""`

### next_start_line

- 类型：正整数
- 含义：编辑起始行号（1-based）
- 注意：光标位置 = startLine 时表示在行前插入

### next_end_line

- 类型：正整数
- 含义：编辑结束行号（1-based）
- 注意：与startLine相等时表示插入模式

### next_content

- 类型：字符串
- 含义：替换内容
- 编码：XML转义或CDATA
- 特殊值：空字符串表示删除

## XML 转义规则

| 原始字符 | 转义后 |
|----------|--------|
| < | `&lt;` |
| > | `&gt;` |
| & | `&amp;` |
| " | `&quot;` |
| ' | `&apos;` |
| 换行 | `&#10;` |
| 回车 | `&#13;` |

## 示例

### 插入示例

**场景**：在第15行后插入新方法

```xml
<actions>
  <next_edit>
    <next_file></next_file>
    <next_start_line>15</next_start_line>
    <next_end_line>15</next_end_line>
    <next_content>  static formatDate(date: Date): string {
    return date.toISOString().split('T')[0]
  }</next_content>
  </next_edit>
</actions>
```

**应用前的代码**：
```typescript
line1
line2
...（第15行）
```

**应用后的代码**：
```typescript
line1
line2
...（第15行）
  static formatDate(date: Date): string {
    return date.toISOString().split('T')[0]
  }
```

### 删除示例

**场景**：删除第10-12行

```xml
<actions>
  <next_edit>
    <next_file></next_file>
    <next_start_line>10</next_start_line>
    <next_end_line>12</next_end_line>
    <next_content></next_content>
  </next_edit>
</actions>
```

### 替换示例

**场景**：替换第5-7行

```xml
<actions>
  <next_edit>
    <next_file></next_file>
    <next_start_line>5</next_start_line>
    <next_end_line>7</next_end_line>
    <next_content>  static validateEmail(email: string): boolean {
    return email.includes('@') && email.includes('.')
  }</next_content>
  </next_edit>
</actions>
```

## 多编辑支持

一个 `<actions>` 块可以包含多个 `<next_edit>`：

```xml
<actions>
  <next_edit>
    <next_file>src/utils/helper.ts</next_file>
    <next_start_line>10</next_start_line>
    <next_end_line>10</next_end_line>
    <next_content>  static formatDate(d: Date): string {
    return d.toISOString()
  }</next_content>
  </next_edit>
  <next_edit>
    <next_file>src/utils/validator.ts</next_file>
    <next_start_line>5</next_start_line>
    <next_end_line>8</next_end_line>
    <next_content></next_content>
  </next_edit>
</actions>
```

## 解析器实现要点

```typescript
class NEXTEditParser {
  static parse(xml: string): NEXTActions {
    const edits: NEXTEdit[] = []
    
    // 1. 提取 actions 块
    const actionsMatch = xml.match(/<actions>([\s\S]*?)<\/actions>/i)
    if (!actionsMatch) return { edits }
    
    // 2. 遍历 next_edit 块
    const editRegex = /<next_edit>([\s\S]*?)<\/next_edit>/gi
    let match
    
    while ((match = editRegex.exec(actionsMatch[1])) !== null) {
      const block = match[1]
      
      // 3. 提取字段
      const file = this.extractTag(block, 'next_file')
      const startLine = parseInt(this.extractTag(block, 'next_start_line'))
      const endLine = parseInt(this.extractTag(block, 'next_end_line'))
      const content = this.decodeContent(this.extractTag(block, 'next_content'))
      
      edits.push({ file, startLine, endLine, content })
    }
    
    return { edits }
  }
  
  private static extractTag(block: string, tag: string): string {
    const regex = new RegExp(`<${tag}>([\\s\\S]*?)</${tag}>`, 'i')
    const match = block.match(regex)
    return match ? match[1].trim() : ''
  }
  
  private static decodeContent(content: string): string {
    return content
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&amp;/g, '&')
      .replace(/&quot;/g, '"')
      .replace(/&apos;/g, "'")
      .replace(/&#10;/g, '\n')
      .replace(/&#13;/g, '\r')
  }
}
```

## 编辑引擎实现要点

```typescript
class NEXTEditEngine {
  static apply(content: string, edits: NEXTEdit[]): string {
    const lines = content.split('\n')
    
    // 按行号倒序排列，避免行号偏移
    const sorted = [...edits].sort((a, b) => b.startLine - a.startLine)
    
    for (const edit of sorted) {
      const start = Math.max(0, edit.startLine - 1)  // 0-based
      const end = Math.max(0, edit.endLine - 1)
      
      if (edit.startLine === edit.endLine && edit.content) {
        // 插入模式
        lines.splice(start, 0, edit.content)
      } else if (!edit.content.trim()) {
        // 删除模式
        lines.splice(start, end - start + 1)
      } else {
        // 替换模式
        const newLines = edit.content.split('\n')
        lines.splice(start, end - start + 1, ...newLines)
      }
    }
    
    return lines.join('\n')
  }
}
```

## 已知限制

1. **行号偏移**：多个编辑时需倒序处理
2. **跨文件编辑**：需要文件锁或事务支持
3. **大文件处理**：建议分批处理
4. **编码问题**：确保统一使用 UTF-8

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2024-01 | 初始版本 |
| 1.1 | 2024-06 | 增加多文件支持 |
| 1.2 | 2024-12 | 增加 CDATA 包装支持 |
