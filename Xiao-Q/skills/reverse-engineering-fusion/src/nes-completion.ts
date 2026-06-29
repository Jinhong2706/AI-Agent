/**
 * NES (Next Edit Suggestion) 协议完整实现
 * 
 * 基于通义灵码的代码补全协议,提供解析、编辑和应用功能
 */

// ==================== 类型定义 ====================

export interface NEXTEdit {
  file: string       // 目标文件(空表示当前文件)
  startLine: number  // 起始行(1-based)
  endLine: number    // 结束行(1-based)
  content: string    // 替换内容
}

export interface NEXTActions {
  edits: NEXTEdit[]
}

export interface NESContext {
  currentFile: string
  cursorLine: number
  cursorColumn: number
  language: string
  codeBeforeCursor: string
  codeAfterCursor: string
  relatedFiles?: { path: string; content: string; snippet: string }[]
  recentDiffs?: { file: string; oldContent: string; newContent: string; timestamp: number }[]
}

export interface MiniMaxConfig {
  baseURL: string
  apiKey: string
  model: string
}

export interface LineDiff {
  line: number
  original: string
  modified: string
  type: 'unchanged' | 'inserted' | 'deleted' | 'replaced'
}

// ==================== 协议解析器 ====================

export class NEXTEditParser {
  /**
   * 解析XML格式的编辑指令
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
        console.warn(`[NEXTEditParser] 编辑${editIndex}:无效的行号 (startLine=${startLineStr}, endLine=${endLineStr})`)
        continue
      }
      
      edits.push({ file, startLine, endLine, content })
    }
    
    return { edits }
  }
  
  /**
   * 提取标签内容(支持XML转义)
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

// ==================== 编辑引擎 ====================

export class NEXTEditEngine {
  /**
   * 将编辑操作应用到文件内容
   */
  static apply(content: string, edits: NEXTEdit[], targetFile: string = ''): string {
    if (!content && content !== '') {
      throw new Error('文件内容不能为空或未定义')
    }
    
    if (!edits || edits.length === 0) {
      return content
    }
    
    const lines = content.split('\n')
    
    // 按行号倒序排列,避免行号偏移
    const sortedEdits = [...edits]
      .filter(e => e.file === '' || e.file === targetFile)
      .sort((a, b) => b.startLine - a.startLine)
    
    for (const edit of sortedEdits) {
      try {
        this.applyEdit(lines, edit)
      } catch (error: any) {
        console.error(`[NEXTEditEngine] 应用编辑失败:`, error.message)
      }
    }
    
    return lines.join('\n')
  }
  
  /**
   * 应用单个编辑操作
   */
  private static applyEdit(lines: string[], edit: NEXTEdit): void {
    // 边界检查
    if (edit.startLine < 1) {
      throw new Error('起始行号必须 >= 1')
    }
    
    if (edit.endLine > lines.length) {
      console.warn(`[NEXTEditEngine] 结束行号(${edit.endLine})超过文件行数(${lines.length})`)
      return
    }
    
    // 转为0-based索引
    const startIdx = Math.max(0, edit.startLine - 1)
    const endIdx = Math.max(0, edit.endLine - 1)
    
    // 语义判断
    if (edit.startLine === edit.endLine && edit.content) {
      // 插入模式:在指定行位置插入新行
      lines.splice(startIdx, 0, edit.content)
    } else if (edit.content.trim() === '') {
      // 删除模式:删除行范围
      lines.splice(startIdx, endIdx - startIdx + 1)
    } else {
      // 替换模式:用新内容替换行范围
      const newLines = edit.content.split('\n')
      lines.splice(startIdx, endIdx - startIdx + 1, ...newLines)
    }
  }
  
  /**
   * 预览编辑效果(不修改原始内容)
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
    const maxLen = Math.max(originalLines.length, modifiedLines.length)
    
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
}

// ==================== Prompt构建器 ====================

export class NESPromptBuilder {
  /**
   * 构建NES专用Prompt
   */
  static buildPrompt(context: NESContext): string {
    let prompt = `You are a code editing AI. The user is writing ${context.language} code.

Current file: ${context.currentFile}
Cursor position: Line ${context.cursorLine}, Column ${context.cursorColumn}

Code before cursor:
${context.codeBeforeCursor}

Code after cursor:
${context.codeAfterCursor}
`

    // 添加相关文件上下文
    if (context.relatedFiles && context.relatedFiles.length > 0) {
      prompt += `\nRelated files:\n`
      for (const file of context.relatedFiles.slice(0, 3)) {
        prompt += `- ${file.path}: ${file.snippet}\n`
      }
    }

    // 添加最近变更上下文
    if (context.recentDiffs && context.recentDiffs.length > 0) {
      prompt += `\nRecent changes:\n`
      for (const diff of context.recentDiffs.slice(0, 3)) {
        const change = diff.oldContent 
          ? `'${diff.oldContent.substring(0, 20)}...' -> '${diff.newContent.substring(0, 20)}...'`
          : 'created'
        prompt += `- ${diff.file}: ${change}\n`
      }
    }

    prompt += `
Task: Predict the next code edit and output ONLY valid XML.
Output format:
<actions>
  <next_edit>
    <next_file></next_file>
    <next_start_line>line number</next_start_line>
    <next_end_line>line number</next_end_line>
    <next_content>new code here</next_content>
  </next_edit>
</actions>

Rules:
- INSERT: startLine = line after which to insert, endLine = same as startLine, content = new code
- DELETE: startLine = first line, endLine = last line, content = empty
- REPLACE: startLine = first line, endLine = last line, content = new code
- No edit needed: <actions></actions>

Output ONLY the XML above, nothing else:`

    return prompt
  }
}

// ==================== MiniMax适配器 ====================

export class MiniMaxAdapter {
  private config: MiniMaxConfig

  constructor(config: MiniMaxConfig) {
    this.config = config
  }

  /**
   * 获取代码补全
   */
  async getCompletion(prompt: string): Promise<string> {
    const url = `${this.config.baseURL}/v1/messages`

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': this.config.apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true'
      },
      body: JSON.stringify({
        model: this.config.model,
        max_tokens: 2000,
        messages: [{ role: 'user', content: prompt }]
      })
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`MiniMax API Error: ${response.status} - ${error}`)
    }

    const data = await response.json()
    
    // MiniMax可能返回thinking或text类型
    if (data.content && data.content[0]) {
      const item = data.content[0]
      return item.thinking || item.text || ''
    }
    
    return ''
  }
}

// 默认配置(从环境变量读取)
export const DEFAULT_MINIMAX_CONFIG: MiniMaxConfig = {
  baseURL: process.env.MINIMAX_BASE_URL || 'https://v2.aicodee.com',
  apiKey: process.env.MINIMAX_API_KEY || '',
  model: process.env.MINIMAX_MODEL || 'MiniMax-M2.7-highspeed'
}

// ==================== 集成系统 ====================

export class NESCompletionSystem {
  private adapter: MiniMaxAdapter

  constructor(adapter: MiniMaxAdapter) {
    this.adapter = adapter
  }

  /**
   * 获取代码补全建议
   */
  async getCompletion(context: NESContext): Promise<{
    actions: NEXTEdit[]
    rawResponse: string
    confidence: number
  }> {
    // 1. 构建Prompt
    const prompt = NESPromptBuilder.buildPrompt(context)
    
    // 2. 调用AI获取响应
    const rawResponse = await this.adapter.getCompletion(prompt)
    
    // 3. 解析XML响应
    const actions = NEXTEditParser.parse(rawResponse)
    
    // 4. 计算置信度
    const confidence = this.calculateConfidence(actions, rawResponse)
    
    return { actions: actions.edits, rawResponse, confidence }
  }

  /**
   * 计算置信度
   */
  private calculateConfidence(actions: NEXTActions, rawResponse: string): number {
    let confidence = 0.5
    
    if (actions.edits.length > 0) {
      confidence += 0.3
    }
    
    if (rawResponse.includes('<actions>') && rawResponse.includes('</actions>')) {
      confidence += 0.2
    }
    
    return Math.min(1.0, confidence)
  }
}
