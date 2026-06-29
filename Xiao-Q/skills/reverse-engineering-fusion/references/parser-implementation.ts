# 协议解析器实现

## 概述

本文件提供 NES（Next Edit Suggestion）协议的完整解析器实现。

## 接口定义

```typescript
export interface NEXTEdit {
  file: string       // 目标文件（空表示当前文件）
  startLine: number  // 起始行（1-based）
  endLine: number    // 结束行（1-based）
  content: string    // 替换内容
}

export interface NEXTActions {
  edits: NEXTEdit[]
}
```

## 完整实现

```typescript
export class NEXTEditParser {
  /**
   * 解析XML格式的编辑指令
   * @param xml NES协议的XML字符串
   * @returns 解析后的编辑操作列表
   */
  static parse(xml: string): NEXTActions {
    const edits: NEXTEdit[] = []
    
    // 匹配 actions 块
    const actionsMatch = xml.match(/<actions>([\s\S]*?)<\/actions>/i)
    if (!actionsMatch) {
      console.warn('[NEXTEditParser] 未找到 <actions> 块')
      return { edits }
    }
    
    const actionsContent = actionsMatch[1]
    
    // 检查是否为空actions
    if (actionsContent.trim() === '') {
      return { edits }
    }
    
    // 匹配 next_edit 块
    const editRegex = /<next_edit>([\s\S]*?)<\/next_edit>/gi
    let match
    let editIndex = 0
    
    while ((match = editRegex.exec(actionsContent)) !== null) {
      editIndex++
      const editBlock = match[1]
      
      // 提取各字段
      const file = this.extractTag(editBlock, 'next_file')
      const startLineStr = this.extractTag(editBlock, 'next_start_line')
      const endLineStr = this.extractTag(editBlock, 'next_end_line')
      const content = this.extractTag(editBlock, 'next_content')
      
      const startLine = parseInt(startLineStr)
      const endLine = parseInt(endLineStr)
      
      // 验证数据有效性
      if (isNaN(startLine) || isNaN(endLine) || startLine <= 0 || endLine <= 0) {
        console.warn(`[NEXTEditParser] 编辑${editIndex}：无效的行号 (startLine=${startLineStr}, endLine=${endLineStr})`)
        continue
      }
      
      edits.push({ file, startLine, endLine, content })
    }
    
    return { edits }
  }
  
  /**
   * 提取标签内容（支持XML转义）
   */
  private static extractTag(block: string, tag: string): string {
    const regex = new RegExp(`<${tag}>([\\s\\S]*?)</${tag}>`, 'i')
    const match = block.match(regex)
    
    if (!match) {
      console.warn(`[NEXTEditParser] 未找到 <${tag}> 标签`)
      return ''
    }
    
    return this.decodeContent(match[1].trim())
  }
  
  /**
   * 解码XML实体
   */
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
  
  /**
   * 验证编辑操作的合法性
   */
  static validate(edits: NEXTEdit[]): { valid: boolean; errors: string[] } {
    const errors: string[] = []
    
    for (let i = 0; i < edits.length; i++) {
      const edit = edits[i]
      
      if (edit.startLine <= 0 || edit.endLine <= 0) {
        errors.push(`编辑${i + 1}：行号必须为正整数`)
      }
      
      if (edit.startLine > edit.endLine) {
        errors.push(`编辑${i + 1}：起始行(${edit.startLine})大于结束行(${edit.endLine})`)
      }
    }
    
    return { valid: errors.length === 0, errors }
  }
  
  /**
   * 将编辑操作序列化为XML
   */
  static serialize(actions: NEXTActions): string {
    let xml = '<actions>\n'
    
    for (const edit of actions.edits) {
      xml += '  <next_edit>\n'
      xml += `    <next_file>${this.encodeContent(edit.file)}</next_file>\n`
      xml += `    <next_start_line>${edit.startLine}</next_start_line>\n`
      xml += `    <next_end_line>${edit.endLine}</next_end_line>\n`
      xml += `    <next_content>${this.encodeContent(edit.content)}</next_content>\n`
      xml += '  </next_edit>\n'
    }
    
    xml += '</actions>'
    return xml
  }
  
  /**
   * 编码XML实体
   */
  private static encodeContent(content: string): string {
    return content
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&apos;')
      .replace(/\n/g, '&#10;')
      .replace(/\r/g, '&#13;')
  }
}
```

## 使用示例

```typescript
// 解析XML
const xml = `<actions>
  <next_edit>
    <next_file></next_file>
    <next_start_line>15</next_start_line>
    <next_end_line>15</next_end_line>
    <next_content>new code here</next_content>
  </next_edit>
</actions>`

const { edits } = NEXTEditParser.parse(xml)
console.log(edits)

// 验证
const { valid, errors } = NEXTEditParser.validate(edits)
if (!valid) {
  console.error('验证失败:', errors)
}

// 序列化
const output = NEXTEditParser.serialize({ edits })
console.log(output)
```

## 依赖

无外部依赖，纯 TypeScript 实现。

## 测试

参见 `../scripts/test-nes.ts`
