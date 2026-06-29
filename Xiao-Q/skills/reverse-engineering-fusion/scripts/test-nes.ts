/**
 * test-nes.ts
 * NES 协议测试脚本
 * 
 * 使用方法：npm test 或 bun run scripts/test-nes.ts
 */

import { 
  NEXTEditParser, 
  NEXTEditEngine, 
  NESPromptBuilder, 
  MiniMaxAdapter, 
  DEFAULT_MINIMAX_CONFIG,
  NESContext 
} from '../src/nes-completion'

async function testParser() {
  console.log('\n========== 测试1：XML解析器 ==========')
  
  const testXML = `
<actions>
  <next_edit>
    <next_file></next_file>
    <next_start_line>15</next_start_line>
    <next_end_line>15</next_end_line>
    <next_content>  static formatDate(date: Date): string {
    return date.toISOString().split('T')[0]
  }</next_content>
  </next_edit>
</actions>`

  const result = NEXTEditParser.parse(testXML)
  console.log('✅ 解析成功!')
  console.log('解析结果:', JSON.stringify(result, null, 2))
  console.log()
}

async function testEngine() {
  console.log('========== 测试2：编辑引擎 ==========')
  
  const originalContent = `line1
line2
line3
line4
line5`

  const edits = [
    { file: '', startLine: 3, endLine: 3, content: 'new line inserted' }
  ]

  const modified = NEXTEditEngine.apply(originalContent, edits)
  
  console.log('原始内容:\n' + originalContent)
  console.log('\n插入第3行后:\n' + modified)
  console.log('✅ 编辑引擎测试通过\n')
}

async function testPrompt() {
  console.log('========== 测试3：Prompt构建器 ==========')
  
  const context: NESContext = {
    currentFile: 'src/utils/helper.ts',
    cursorLine: 5,
    cursorColumn: 10,
    language: 'typescript',
    codeBeforeCursor: `export class Helper {
  static async findUser(id: string) {
    return db.query('SELECT * FROM users WHERE id = ?', [id])
  }

  static validateEmail(email: string) {
    return email.includes('@')
  }

  static `,
    codeAfterCursor: `formatDate(date) {
    return date.toISOString()
  }
}`
  }

  const prompt = NESPromptBuilder.buildPrompt(context)
  console.log('生成的Prompt（前500字符）:\n' + prompt.substring(0, 500) + '...')
  console.log('✅ Prompt构建器测试通过\n')
}

async function testMiniMaxAPI() {
  console.log('========== 测试4：MiniMax API ==========')
  
  // 检查是否配置了API Key
  if (!DEFAULT_MINIMAX_CONFIG.apiKey || DEFAULT_MINIMAX_CONFIG.apiKey === '') {
    console.log('⚠️  未配置 MiniMax API Key，跳过此测试')
    console.log('💡 请复制 .env.example 到 .env 并填写你的 API Key\n')
    return
  }
  
  const adapter = new MiniMaxAdapter(DEFAULT_MINIMAX_CONFIG)
  
  try {
    const result = await adapter.getCompletion('Say hello in exactly 3 words')
    console.log('API响应:', result.substring(0, 200))
    console.log('✅ MiniMax API测试通过\n')
  } catch (error: any) {
    console.log('❌ API调用失败:', error.message)
    console.log('💡 请检查 .env 文件中的 API Key 是否正确\n')
  }
}

async function main() {
  console.log('========================================')
  console.log('  NES 协议测试套件 v2.0')
  console.log('========================================\n')

  await testParser()
  await testEngine()
  await testPrompt()
  await testMiniMaxAPI()

  console.log('========================================')
  console.log('  ✅ 测试完成')
  console.log('========================================\n')
}

main().catch(console.error)
