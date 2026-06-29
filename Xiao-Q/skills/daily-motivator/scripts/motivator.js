#!/usr/bin/env node

/**
 * Daily Motivator - Skill 脚本
 * 
 * 供 SKILL.md 调用的命令行工具，三个子命令：
 *   node motivator.js quote     --category <work|life|monday|friday> --count <n>
 *   node motivator.js countdown --date <YYYY-MM-DD> --event <名称>
 *   node motivator.js cheer     --members '<JSON>'
 */

// ===== 金句库 =====
const QUOTES = {
  work: [
    "🔥 今天的代码，就是明天的产品。每一行都值得认真对待。",
    "💪 Bug 不可怕，可怕的是不敢面对 Bug 的心。",
    "🚀 伟大的产品都是一个个小迭代堆出来的，今天又进步了一点！",
    "⚡ 最好的优化不是让代码更快，而是让用户更爽。",
    "🎯 需求会变，deadline 会来，但你的成长不会白费。",
    "🌟 写代码就像写故事，逻辑清晰的代码自己会说话。",
    "🏆 不要等到完美才发布，先完成，再完美。",
    "💡 今天学到的每个新知识，都是未来解决问题的武器。"
  ],
  life: [
    "☀️ 生活不止眼前的 KPI，还有诗和远方的 OKR。",
    "🌈 再忙也要记得喝水、站起来走走。身体是革命的本钱！",
    "🍃 适当摸鱼不是偷懒，是给大脑做垃圾回收。",
    "🎵 下班后的时间属于你自己，好好享受！",
    "🌙 今天辛苦了，早点休息，明天又是元气满满的一天。",
    "🏃 运动一下吧！跑步时大脑会帮你解 Bug 的。"
  ],
  monday: [
    "📅 周一快乐！新的一周，新的开始，冲冲冲！",
    "☕ 周一综合症？一杯咖啡就能治好。",
    "🎮 把这周当成一局游戏，每天完成一个关卡！"
  ],
  friday: [
    "🎉 周五啦！坚持就是胜利，周末就在眼前！",
    "🍻 今天的代码写完了吗？写完就可以快乐周末了！",
    "🌴 周末计划想好了吗？工作是为了更好地生活。"
  ]
};

const CHEER_TEMPLATES = [
  "🎖️ {name}，你最近的表现太棒了！{reason}，继续保持！",
  "💪 {name} 加油！{reason}，团队因你而更强！",
  "🌟 感谢 {name}！{reason}，你是团队的宝藏！",
  "🚀 {name}，{reason}，这份努力大家都看在眼里！",
  "👏 为 {name} 鼓掌！{reason}，未来可期！",
  "🏅 {name}，你做到了！{reason}，继续冲！"
];

// ===== 参数解析 =====
function parseArgs(args) {
  const result = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith('--')) {
      const key = args[i].slice(2);
      result[key] = args[i + 1] || '';
      i++;
    }
  }
  return result;
}

// ===== 子命令 =====
function cmdQuote(opts) {
  const count = Math.min(Math.max(parseInt(opts.count) || 1, 1), 5);
  let category = opts.category;

  if (!category) {
    const day = new Date().getDay();
    if (day === 1) category = 'monday';
    else if (day === 5) category = 'friday';
    else category = Math.random() > 0.5 ? 'work' : 'life';
  }

  const pool = QUOTES[category] || QUOTES.work;
  const shuffled = [...pool].sort(() => Math.random() - 0.5);
  const selected = shuffled.slice(0, count);

  const names = { work: '💼 工作激励', life: '🌿 生活感悟', monday: '📅 周一特供', friday: '🎉 周五特供' };
  console.log(`${names[category] || '✨ 金句'}`);
  console.log('─'.repeat(30));
  selected.forEach((q, i) => console.log(`${i + 1}. ${q}`));
  console.log('─'.repeat(30));
  console.log('💬 每句话都是一粒种子，愿它在你心里生根发芽。');
}

function cmdCountdown(opts) {
  const { date, event } = opts;
  if (!date || !event) {
    console.log('❌ 用法: node motivator.js countdown --date YYYY-MM-DD --event 事件名');
    process.exit(1);
  }

  const target = new Date(date + 'T00:00:00');
  const now = new Date();
  now.setHours(0, 0, 0, 0);

  const diffDays = Math.round((target - now) / (1000 * 60 * 60 * 24));

  let emoji, msg;
  if (diffDays < 0) {
    emoji = '⏰'; msg = `「${event}」已经过去 ${Math.abs(diffDays)} 天了！`;
  } else if (diffDays === 0) {
    emoji = '🎊'; msg = `🎊🎊🎊 今天就是「${event}」！！！`;
  } else if (diffDays <= 3) {
    emoji = '🔥'; msg = `距离「${event}」仅剩 ${diffDays} 天！冲刺阶段！`;
  } else if (diffDays <= 7) {
    emoji = '⚡'; msg = `距离「${event}」还有 ${diffDays} 天，进入最后一周！`;
  } else if (diffDays <= 30) {
    emoji = '📅'; msg = `距离「${event}」还有 ${diffDays} 天（${Math.floor(diffDays / 7)} 周 ${diffDays % 7} 天），节奏稳住！`;
  } else {
    emoji = '🗓️'; msg = `距离「${event}」还有 ${diffDays} 天（约 ${Math.round(diffDays / 30)} 个月），从容规划！`;
  }

  const tips = [
    "每一天的努力都在缩短这个数字 💪",
    "不急不躁，按计划推进就好 🎯",
    "想想完成后的成就感，是不是充满动力？ 🚀",
    "把大目标拆成小任务，一步一个脚印 👣"
  ];

  console.log(`${emoji} 倒计时`);
  console.log('─'.repeat(30));
  console.log(msg);
  console.log(`📆 目标: ${date}  📍 今天: ${now.toISOString().slice(0, 10)}`);
  console.log(`💬 ${tips[Math.floor(Math.random() * tips.length)]}`);
}

function cmdCheer(opts) {
  let members;
  try {
    members = JSON.parse(opts.members);
  } catch {
    console.log('❌ --members 参数需要是 JSON 数组');
    console.log('示例: --members \'[{"name":"小明","reason":"修复了线上Bug"}]\'');
    process.exit(1);
  }

  console.log('👥 团队鼓励时刻');
  console.log('═'.repeat(30));
  members.forEach(m => {
    const tpl = CHEER_TEMPLATES[Math.floor(Math.random() * CHEER_TEMPLATES.length)];
    console.log(tpl.replace('{name}', m.name).replace('{reason}', m.reason));
    console.log('');
  });
  console.log('═'.repeat(30));
  console.log('🎉 每个人都是不可替代的力量！');
}

// ===== 入口 =====
const [subcommand, ...rest] = process.argv.slice(2);
const opts = parseArgs(rest);

switch (subcommand) {
  case 'quote':     cmdQuote(opts);     break;
  case 'countdown': cmdCountdown(opts); break;
  case 'cheer':     cmdCheer(opts);     break;
  default:
    console.log('🌟 Daily Motivator - 每日金句 & 团队鼓励器');
    console.log('');
    console.log('用法:');
    console.log('  node motivator.js quote     [--category work|life|monday|friday] [--count 3]');
    console.log('  node motivator.js countdown --date 2026-05-01 --event 五一假期');
    console.log('  node motivator.js cheer     --members \'[{"name":"小明","reason":"修复线上Bug"}]\'');
}
