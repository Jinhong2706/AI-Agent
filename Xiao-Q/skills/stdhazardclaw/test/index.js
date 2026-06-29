/**
 * 隐患虾技能测试
 */

const skill = require('../src/index').default;

async function runTests() {
  console.log('🧪 开始测试 stdhazardclaw 技能...\n');

  // 测试1: 文本分析
  console.log('📝 测试1: 文本隐患分析');
  const textInput = {
    type: 'text',
    content: '电焊作业时没有接漏电保护开关，火花飞溅到旁边的人员身上'
  };

  const textResult = await skill.handle(textInput);
  console.log('输入:', textInput.content);
  console.log('输出:', JSON.stringify(textResult, null, 2));
  console.log('✅ 文本分析测试完成\n');

  // 测试2: 图片分析（模拟）
  console.log('📸 测试2: 图片隐患分析');
  const imageInput = {
    type: 'image',
    content: 'base64_encoded_image_data_placeholder'
  };

  const imageResult = await skill.handle(imageInput);
  console.log('输出:', JSON.stringify(imageResult, null, 2));
  console.log('✅ 图片分析测试完成\n');

  // 测试3: 无隐患情况
  console.log('✨ 测试3: 无隐患场景');
  const noHazardInput = {
    type: 'text',
    content: '今天天气很好，办公室环境整洁'
  };

  const noHazardResult = await skill.handle(noHazardInput);
  console.log('输入:', noHazardInput.content);
  console.log('输出:', JSON.stringify(noHazardResult, null, 2));
  console.log('✅ 无隐患测试完成\n');

  // 汇总
  const allPassed = textResult.type === 'success' &&
                    imageResult.type === 'success' &&
                    noHazardResult.type === 'success';

  console.log('═══════════════════════════════════');
  console.log(allPassed ? '✅ 所有测试通过!' : '❌ 部分测试失败');
  console.log('═══════════════════════════════════');
}

// 运行测试
runTests().catch(console.error);
