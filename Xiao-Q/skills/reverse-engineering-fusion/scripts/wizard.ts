/**
 * ORRI 工作流向导 - 交互式引导执行逆向工程融合
 * 
 * 使用方法: npm run wizard
 */

import * as fs from 'fs'
import * as path from 'path'
import * as readline from 'readline'

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
})

function question(query: string): Promise<string> {
  return new Promise((resolve) => {
    rl.question(query, (answer) => {
      resolve(answer.trim())
    })
  })
}

// ==================== 颜色输出 ====================

const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
}

function log(color: string, message: string) {
  console.log(`${color}${message}${colors.reset}`)
}

function header(title: string) {
  console.log('\n' + '='.repeat(60))
  log(colors.bright + colors.cyan, `  ${title}`)
  console.log('='.repeat(60) + '\n')
}

function step(number: number, title: string) {
  log(colors.bright + colors.blue, `\n📍 Step ${number}: ${title}`)
  console.log('-'.repeat(60))
}

function success(message: string) {
  log(colors.green, `✅ ${message}`)
}

function warning(message: string) {
  log(colors.yellow, `⚠️  ${message}`)
}

function error(message: string) {
  log(colors.red, `❌ ${message}`)
}

// ==================== 工作流 ====================

async function runWizard() {
  header('🚀 ORRI 逆向工程融合工作流向导')
  
  log(colors.cyan, '本向导将引导您完成完整的逆向工程融合流程')
  log(colors.cyan, '每个步骤都会生成相应的文档\n')
  
  // 收集基本信息
  const projectName = await question('📝 项目名称: ')
  const targetSystem = await question('🎯 目标系统: ')
  const targetPath = await question('📂 目标系统路径 (可选): ')
  const goal = await question('🎯 融合目标 (一句话描述): ')
  
  console.log()
  
  // Step 1: Observation
  await executeObservation(projectName, targetSystem, targetPath)
  
  // Step 2: Reverse
  await executeReverse(projectName, targetSystem)
  
  // Step 3: Reconstruct
  await executeReconstruct(projectName, targetSystem, goal)
  
  // Step 4: Innovate
  await executeInnovate(projectName, targetSystem, goal)
  
  // 完成
  await finishProject(projectName)
  
  rl.close()
}

// ==================== Step 1: Observation ====================

async function executeObservation(projectName: string, targetSystem: string, targetPath: string) {
  step(1, 'Observation (观察) - 只看不改')
  
  log(colors.yellow, '请回答以下问题,我们将生成 observation-notes.md\n')
  
  const techStack = await question('💻 技术栈 (语言/框架/工具): ')
  const entryFile = await question('🚪 入口文件: ')
  const configFile = await question('⚙️  配置文件: ')
  const docFile = await question('📄 文档文件: ')
  const inputFormat = await question('📥 输入格式: ')
  const outputFormat = await question('📤 输出格式: ')
  const dataFlow = await question('🔄 数据流向 (简述): ')
  const boundaryConditions = await question('⚠️  边界条件 (正常/异常/极端): ')
  
  // 生成文档
  const content = `# 观察笔记 - ${targetSystem}

## 基本信息
- 项目名称: ${projectName}
- 目标系统: ${targetSystem}
- 目标路径: ${targetPath || '未指定'}
- 技术栈: ${techStack}
- 观察日期: ${new Date().toISOString().split('T')[0]}

## 目录结构
\`\`\`
[请手动粘贴目录树]
\`\`\`

## 关键文件
- 入口文件: ${entryFile}
- 配置文件: ${configFile}
- 文档文件: ${docFile}

## 输入/输出
- 输入格式: ${inputFormat}
- 输出格式: ${outputFormat}
- 数据流向: ${dataFlow}

## 边界条件
${boundaryConditions}

## 初步判断
- 核心功能: [待补充]
- 关键模块: [待补充]
- 潜在风险: [待补充]

## 下一步
- [ ] 进入 Step 2: Reverse (逆向)
`
  
  const outputPath = path.join(process.cwd(), 'output', projectName, 'observation-notes.md')
  fs.mkdirSync(path.dirname(outputPath), { recursive: true })
  fs.writeFileSync(outputPath, content, 'utf-8')
  
  success(`已生成: ${outputPath}`)
  log(colors.cyan, '💡 提示: 可以手动补充目录结构和更多细节\n')
  
  await question('按回车继续...')
}

// ==================== Step 2: Reverse ====================

async function executeReverse(projectName: string, targetSystem: string) {
  step(2, 'Reverse (逆向) - 提取协议和架构')
  
  log(colors.yellow, '请回答以下问题,我们将生成 protocol.md\n')
  
  const protocolType = await question('📋 协议类型 (XML/JSON/二进制/其他): ')
  const protocolVersion = await question('🔢 协议版本: ')
  const requestFormat = await question('📨 请求格式 (示例): ')
  const responseFormat = await question('📩 响应格式 (示例): ')
  const fields = await question('📊 主要字段 (逗号分隔): ')
  const semanticRules = await question('📐 语义规则 (简述): ')
  const errorCodes = await question('❌ 错误码 (如有): ')
  
  // 生成文档
  const content = `# 协议规范 - ${targetSystem}

## 协议概述
- 项目名称: ${projectName}
- 协议类型: ${protocolType}
- 协议版本: ${protocolVersion}
- 用途: [待补充]

## 消息格式

### 请求格式
\`\`\`${protocolType.toLowerCase()}
${requestFormat}
\`\`\`

### 响应格式
\`\`\`${protocolType.toLowerCase()}
${responseFormat}
\`\`\`

## 字段说明

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
${fields.split(',').map(f => `| ${f.trim()} | - | - | - | - |`).join('\n')}

## 语义规则
${semanticRules}

## 错误码
${errorCodes || '暂无'}

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| ${protocolVersion} | ${new Date().toISOString().split('T')[0]} | 初始提取 |

## 下一步
- [ ] 进入 Step 3: Reconstruct (重建)
`
  
  const outputPath = path.join(process.cwd(), 'output', projectName, 'protocol.md')
  fs.writeFileSync(outputPath, content, 'utf-8')
  
  success(`已生成: ${outputPath}`)
  log(colors.cyan, '💡 提示: 可以手动补充更多字段和规则\n')
  
  await question('按回车继续...')
}

// ==================== Step 3: Reconstruct ====================

async function executeReconstruct(projectName: string, targetSystem: string, goal: string) {
  step(3, 'Reconstruct (重建) - 用自己的技术栈实现')
  
  log(colors.yellow, '请回答以下问题,我们将生成 implementation.md\n')
  
  const ourTechStack = await question('💻 我们的技术栈: ')
  const architecture = await question('🏗️  架构模式 (MVC/MVVM/微服务等): ')
  const modules = await question('📦 核心模块 (逗号分隔): ')
  const testCoverage = await question('🧪 测试覆盖率目标 (%): ')
  const compatibility = await question('✅ 兼容性要求: ')
  
  // 生成文档
  const content = `# 实施报告 - ${targetSystem}

## 实现概述
- 项目名称: ${projectName}
- 融合目标: ${goal}
- 技术栈: ${ourTechStack}
- 架构模式: ${architecture}
- 实施日期: ${new Date().toISOString().split('T')[0]}

## 模块实现

${modules.split(',').map((m, i) => `### ${i + 1}. ${m.trim()}
- 职责: [待补充]
- 接口: [待补充]
- 依赖: [待补充]
- 文件: \`src/${m.trim().toLowerCase()}.ts\`
`).join('\n')}

## 测试结果

| 测试类型 | 用例数 | 通过率 | 说明 |
|----------|--------|--------|------|
| 单元测试 | - | - | 目标: ${testCoverage}% |
| 集成测试 | - | - | - |
| 兼容性测试 | - | - | ${compatibility} |

## 性能对比

| 指标 | 原系统 | 我们的系统 | 提升 |
|------|--------|-----------|------|
| 响应时间 | - | - | - |
| 内存占用 | - | - | - |
| 代码行数 | - | - | - |

## 已知限制
- [待补充]

## 下一步
- [ ] 进入 Step 4: Innovate (创新)
`
  
  const outputPath = path.join(process.cwd(), 'output', projectName, 'implementation.md')
  fs.writeFileSync(outputPath, content, 'utf-8')
  
  success(`已生成: ${outputPath}`)
  log(colors.cyan, '💡 提示: 实现完成后更新测试结果和性能对比\n')
  
  await question('按回车继续...')
}

// ==================== Step 4: Innovate ====================

async function executeInnovate(projectName: string, targetSystem: string, goal: string) {
  step(4, 'Innovate (创新) - 优化改进,建立壁垒')
  
  log(colors.yellow, '请回答以下问题,我们将生成 architecture.md 和 maintenance.md\n')
  
  const improvements = await question('✨ 改进点 (逗号分隔): ')
  const newFeatures = await question('🆕 新增功能 (逗号分隔): ')
  const advantages = await question('🏆 独特优势 (逗号分隔): ')
  const designDecisions = await question('🎯 关键设计决策 (简述): ')
  
  // 生成 architecture.md
  const archContent = `# 架构设计 - ${targetSystem}

## 设计理念
- 项目名称: ${projectName}
- 融合目标: ${goal}
- 核心思想: [待补充]
- 设计原则: [待补充]

## 架构图

\`\`\`
[请手动绘制架构图]
\`\`\`

## 模块设计

${improvements.split(',').map((imp, i) => `### 改进点 ${i + 1}: ${imp.trim()}
- 背景: [待补充]
- 方案: [待补充]
- 效果: [待补充]
`).join('\n')}

## 新增功能

${newFeatures.split(',').map((feat, i) => `### 功能 ${i + 1}: ${feat.trim()}
- 描述: [待补充]
- 实现: [待补充]
- 价值: [待补充]
`).join('\n')}

## 设计决策

${designDecisions}

## 独特优势

${advantages.split(',').map((adv, i) => `- **优势 ${i + 1}**: ${adv.trim()}`).join('\n')}

## 扩展点
- [待补充]

## 演进路线
- v1.0: 基础功能
- v2.0: 性能优化
- v3.0: 生态建设
`
  
  const archPath = path.join(process.cwd(), 'output', projectName, 'architecture.md')
  fs.writeFileSync(archPath, archContent, 'utf-8')
  success(`已生成: ${archPath}`)
  
  // 生成 maintenance.md
  const maintContent = `# 维护指南 - ${targetSystem}

## 项目信息
- 项目名称: ${projectName}
- 目标系统: ${targetSystem}
- 创建日期: ${new Date().toISOString().split('T')[0]}

## 升级注意事项
- [待补充]

## 故障排查

### 常见问题
- Q1: [待补充]
  - A: [待补充]

## 监控指标
- [待补充]

## 备份策略
- 频率: [待补充]
- 方式: [待补充]

## 联系方式
- 负责人: [待补充]
- 邮箱: [待补充]
`
  
  const maintPath = path.join(process.cwd(), 'output', projectName, 'maintenance.md')
  fs.writeFileSync(maintPath, maintContent, 'utf-8')
  success(`已生成: ${maintPath}`)
  
  log(colors.cyan, '💡 提示: 后续根据实际使用情况补充内容\n')
  
  await question('按回车继续...')
}

// ==================== 完成 ====================

async function finishProject(projectName: string) {
  header('🎉 项目完成!')
  
  const outputDir = path.join(process.cwd(), 'output', projectName)
  
  log(colors.green, `项目目录: ${outputDir}\n`)
  log(colors.cyan, '生成的文档:')
  
  const files = ['observation-notes.md', 'protocol.md', 'implementation.md', 'architecture.md', 'maintenance.md']
  files.forEach(file => {
    const exists = fs.existsSync(path.join(outputDir, file))
    console.log(`  ${exists ? '✅' : '❌'} ${file}`)
  })
  
  console.log()
  log(colors.yellow, '📝 后续步骤:')
  console.log('  1. 补充文档中的 [待补充] 部分')
  console.log('  2. 实现代码并运行测试')
  console.log('  3. 更新性能和测试结果')
  console.log('  4. 部署和维护\n')
  
  log(colors.bright + colors.green, '✨ 恭喜!您已完成 ORRI 逆向工程融合流程!\n')
}

// ==================== 启动 ====================

runWizard().catch((err) => {
  error(`错误: ${err.message}`)
  console.error(err)
  rl.close()
  process.exit(1)
})
