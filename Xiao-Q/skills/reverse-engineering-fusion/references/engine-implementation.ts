# 编辑引擎实现

## 概述

本文件提供 NES（Next Edit Suggestion）协议的编辑应用引擎实现。

## 接口定义

```typescript
import { NEXTEdit, NEXTActions } from './parser-implementation'

export interface EditResult {
  success: boolean
  content: string
  appliedEdits: number
  errors: string[]
}

export interface LineDiff {
  line: number
  original: string
  modified: string
  type: 'unchanged' | 'inserted' | 'deleted' | 'replaced'
}
```

## 完整实现

```typescript
export class NEXTEditEngine {
  /**
   * 将编辑操作应用到文件内容
   * 
   * @param content 原始文件内容
   * @param edits 编辑操作列表
   * @param targetFile 目标文件（用于过滤多文件编辑）
   * @returns 修改后的文件内容
   */
  static apply(content: string, edits: NEXTEdit[], targetFile: string = ''): string {
    // 验证输入
    if (!content && content !== '') {
      throw new Error('文件内容不能为空或未定义')
    }
    
    if (!edits || edits.length === 0) {
      return content
    }
    
    const lines = content.split('\n')
    
    // 按行号倒序排列，避免行号偏移
    const sortedEdits = [...edits]
      .filter(e => e.file === '' || e.file === targetFile)
      .sort((a, b) => b.startLine - a.startLine)
    
    let appliedCount = 0
    
    for (const edit of sortedEdits) {
      try {
        const result = this.applyEdit(lines, edit)
        if (result.success) {
          appliedCount++
        }
      } catch (error: any) {
        console.error(`[NEXTEditEngine] 应用编辑失败:`, error.message)
      }
    }
    
    return lines.join('\n')
  }
  
  /**
   * 应用单个编辑操作
   */
  private static applyEdit(lines: string[], edit: NEXTEdit): { success: boolean; error?: string } {
    // 边界检查
    if (edit.startLine < 1) {
      return { success: false, error: '起始行号必须 >= 1' }
    }
    
    if (edit.endLine > lines.length) {
      return { success: false, error: `结束行号(${edit.endLine})超过文件行数(${lines.length})` }
    }
    
    // 转为0-based索引
    const startIdx = Math.max(0, edit.startLine - 1)
    const endIdx = Math.max(0, edit.endLine - 1)
    
    // 语义判断：
    // 1. startLine == endLine 且 content 非空 → 插入
    // 2. startLine != endLine 且 content 为空 → 删除
    // 3. startLine != endLine 且 content 非空 → 替换
    
    if (edit.startLine === edit.endLine && edit.content) {
      // 插入模式：在指定行位置插入新行
      lines.splice(startIdx, 0, edit.content)
    } else if (edit.content.trim() === '') {
      // 删除模式：删除行范围
      lines.splice(startIdx, endIdx - startIdx + 1)
    } else {
      // 替换模式：用新内容替换行范围
      const newLines = edit.content.split('\n')
      lines.splice(startIdx, endIdx - startIdx + 1, ...newLines)
    }
    
    return { success: true }
  }
  
  /**
   * 预览编辑效果（不修改原始内容）
   */
  static preview(content: string, edits: NEXTEdit[]): {
    original: string
    modified: string
    diffs: LineDiff[]
    appliedCount: number
  } {
    const modified = this.apply(content, edits)
    const originalLines = content.split('\n')
    const modifiedLines = modified.split('\n')
    
    const diffs: LineDiff[] = []
    let maxLen = Math.max(originalLines.length, modifiedLines.length)
    
    for (let i = 0; i < maxLen; i++) {
      const original = originalLines[i] || ''
      const modifiedLine = modifiedLines[i] || ''
      
      let type: LineDiff['type'] = 'unchanged'
      if (i >= originalLines.length) {
        type = 'inserted'
      } else if (i >= modifiedLines.length) {
        type = 'deleted'
      } else if (original !== modifiedLine) {
        type = 'replaced'
      }
      
      diffs.push({
        line: i + 1,
        original,
        modified: modifiedLine,
        type
      })
    }
    
    return {
      original: content,
      modified,
      diffs,
      appliedCount: edits.length
    }
  }
  
  /**
   * 验证编辑操作的合法性
   */
  static validate(content: string, edits: NEXTEdit[]): {
    valid: boolean
    errors: string[]
    warnings: string[]
  } {
    const errors: string[] = []
    const warnings: string[] = []
    const lines = content.split('\n')
    
    for (let i = 0; i < edits.length; i++) {
      const edit = edits[i]
      
      // 检查行号范围
      if (edit.startLine < 1) {
        errors.push(`编辑${i + 1}：起始行号(${edit.startLine})必须 >= 1`)
      }
      
      if (edit.endLine < 1) {
        errors.push(`编辑${i + 1}：结束行号(${edit.endLine})必须 >= 1`)
      }
      
      if (edit.startLine > lines.length) {
        warnings.push(`编辑${i + 1}：起始行号(${edit.startLine})超过文件行数(${lines.length})`)
      }
      
      if (edit.endLine > lines.length) {
        warnings.push(`编辑${i + 1}：结束行号(${edit.endLine})超过文件行数(${lines.length})`)
      }
      
      // 检查插入vs删除语义
      if (edit.startLine === edit.endLine && !edit.content.trim()) {
        warnings.push(`编辑${i + 1}：插入模式但内容为空，可能是误用`)
      }
    }
    
    return {
      valid: errors.length === 0,
      errors,
      warnings
    }
  }
  
  /**
   * 计算编辑后的行号映射（用于追踪变化）
   */
  static mapLines(edits: NEXTEdit[], originalLine: number): number | null {
    // 按行号排序（正序）
    const sortedEdits = [...edits].sort((a, b) => a.startLine - b.startLine)
    
    let offset = 0
    
    for (const edit of sortedEdits) {
      if (edit.startLine > originalLine + offset) {
        break
      }
      
      const editLines = edit.endLine - edit.startLine + 1
      const newLines = edit.content ? edit.content.split('\n').length : 0
      
      offset += newLines - editLines
    }
    
    const mapped = originalLine + offset
    return mapped > 0 ? mapped : null
  }
}
```

## 使用示例

```typescript
// 基本用法
const original = `line1
line2
line3
line4
line5`

const edits = [
  { file: '', startLine: 3, endLine: 3, content: 'new line inserted' }
]

const modified = NEXTEditEngine.apply(original, edits)
console.log(modified)

// 预览
const preview = NEXTEditEngine.preview(original, edits)
console.log(preview.diffs)

// 验证
const validation = NEXTEditEngine.validate(original, edits)
console.log(validation)

// 行号映射
const mappedLine = NEXTEditEngine.mapLines(edits, 4)
console.log(`原始第4行 -> 编辑后第${mappedLine}行`)
```

## 语义规则

| startLine | endLine | content | 操作 |
|-----------|---------|---------|------|
| N | N | 非空 | **插入**：在第N行**后**插入 |
| N | M | 空 | **删除**：删除第N到M行 |
| N | M | 非空 | **替换**：用新内容替换第N到M行 |

## 注意事项

1. **行号偏移**：多个编辑必须倒序处理
2. **多文件编辑**：使用 `targetFile` 参数过滤
3. **语义一致性**：确保 content 非空时表示替换/插入，为空时表示删除

## 依赖

- `NEXTEdit`, `NEXTActions` from `parser-implementation.ts`

## 测试

参见 `../scripts/test-nes.ts`
