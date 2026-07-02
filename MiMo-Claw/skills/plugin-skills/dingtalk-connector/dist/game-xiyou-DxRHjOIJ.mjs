import * as fs from "fs";
import * as path from "path";
import { createHash, createHmac, randomBytes } from "crypto";
import * as os from "os";
//#region src/game-xiyou/uid-resolver.ts
/**
* UID 解析与绑定
*
* 优先级链：
* 1. 钉钉 userId（通过 connector 的 device-auth 获取）
* 2. 本机 fingerprint（兜底，基于 hostname + username 的 SHA256）
*/
const SALT = "xiyou-salt-2026";
/**
* 根据原始 UID 生成稳定的哈希标识
*/
function hashUid(rawUid) {
	return createHash("sha256").update(rawUid + SALT).digest("hex").slice(0, 16);
}
/**
* 生成本机指纹作为兜底 UID
*/
function generateMachineFingerprint() {
	return `machine:${os.hostname()}:${os.userInfo().username}`;
}
/**
* 解析用户 UID
*
* @param senderId - 钉钉消息的发送者 ID（优先使用）
* @returns 稳定的 UID 哈希值（16 位 hex）
*/
function resolveUid(senderId) {
	return hashUid(senderId || generateMachineFingerprint());
}
//#endregion
//#region src/game-xiyou/bounty-system.ts
/**
* 悬赏令系统 (v2)
*
* 每日刷新 3 张悬赏令（铜/银/金），为日常使用增加目标感和方向性。
* 使用基于 UID + 日期的种子随机，确保同一用户同一天结果一致。
*/
const BRONZE_POOL = [
	{
		id: "B001",
		tier: "bronze",
		descriptionTemplate: "成功执行 3 次任意 dws 命令",
		reward: { exp: 15 },
		condition: {
			type: "command",
			count: 3
		}
	},
	{
		id: "B002",
		tier: "bronze",
		descriptionTemplate: "使用 {product} 成功执行 1 次命令",
		reward: { exp: 10 },
		condition: {
			type: "command",
			count: 1
		},
		hasProductPlaceholder: true
	},
	{
		id: "B003",
		tier: "bronze",
		descriptionTemplate: "收服 1 只任意妖怪",
		reward: { exp: 10 },
		condition: {
			type: "capture",
			count: 1
		}
	},
	{
		id: "B004",
		tier: "bronze",
		descriptionTemplate: "达成 3 连击",
		reward: { exp: 20 },
		condition: {
			type: "combo",
			count: 3
		}
	},
	{
		id: "B005",
		tier: "bronze",
		descriptionTemplate: "使用 2 种不同产品的命令",
		reward: { exp: 15 },
		condition: {
			type: "product_variety",
			count: 2
		}
	},
	{
		id: "B006",
		tier: "bronze",
		descriptionTemplate: "收服 1 只精良及以上妖怪",
		reward: { exp: 20 },
		condition: {
			type: "capture",
			qualityMin: "fine",
			count: 1
		}
	},
	{
		id: "B007",
		tier: "bronze",
		descriptionTemplate: "成功执行 5 次任意 dws 命令",
		reward: { exp: 25 },
		condition: {
			type: "command",
			count: 5
		}
	},
	{
		id: "B008",
		tier: "bronze",
		descriptionTemplate: "收服 2 只任意妖怪（不含逃跑）",
		reward: { exp: 20 },
		condition: {
			type: "capture",
			count: 2
		}
	}
];
const SILVER_POOL = [
	{
		id: "B101",
		tier: "silver",
		descriptionTemplate: "收服 1 只稀有及以上妖怪",
		reward: { exp: 50 },
		condition: {
			type: "capture",
			qualityMin: "rare",
			count: 1
		}
	},
	{
		id: "B102",
		tier: "silver",
		descriptionTemplate: "达成 5 连击",
		reward: { exp: 40 },
		condition: {
			type: "combo",
			count: 5
		}
	},
	{
		id: "B103",
		tier: "silver",
		descriptionTemplate: "使用 3 种不同产品的命令",
		reward: { exp: 35 },
		condition: {
			type: "product_variety",
			count: 3
		}
	},
	{
		id: "B104",
		tier: "silver",
		descriptionTemplate: "收服 1 只与 {product} 关联的妖怪",
		reward: { exp: 30 },
		condition: {
			type: "capture",
			count: 1
		},
		hasProductPlaceholder: true
	},
	{
		id: "B105",
		tier: "silver",
		descriptionTemplate: "成功执行 10 次任意 dws 命令",
		reward: { exp: 50 },
		condition: {
			type: "command",
			count: 10
		}
	},
	{
		id: "B106",
		tier: "silver",
		descriptionTemplate: "收服 3 只不同品质的妖怪",
		reward: { exp: 45 },
		condition: {
			type: "quality_variety",
			count: 3
		}
	},
	{
		id: "B107",
		tier: "silver",
		descriptionTemplate: "触发 1 次神仙机缘",
		reward: { exp: 40 },
		condition: {
			type: "encounter",
			count: 1
		}
	},
	{
		id: "B108",
		tier: "silver",
		descriptionTemplate: "收服 1 只图鉴中未拥有的新妖怪",
		reward: { exp: 60 },
		condition: {
			type: "capture",
			count: 1,
			isNew: true
		}
	}
];
const GOLD_POOL = [
	{
		id: "B201",
		tier: "gold",
		descriptionTemplate: "收服 1 只史诗及以上妖怪",
		reward: {
			exp: 100,
			treasureFragment: "random"
		},
		condition: {
			type: "capture",
			qualityMin: "epic",
			count: 1
		}
	},
	{
		id: "B202",
		tier: "gold",
		descriptionTemplate: "达成 10 连击",
		reward: { exp: 80 },
		condition: {
			type: "combo",
			count: 10
		}
	},
	{
		id: "B203",
		tier: "gold",
		descriptionTemplate: "使用 5 种不同产品的命令",
		reward: { exp: 70 },
		condition: {
			type: "product_variety",
			count: 5
		}
	},
	{
		id: "B204",
		tier: "gold",
		descriptionTemplate: "单日收服 5 只不同妖怪",
		reward: { exp: 100 },
		condition: {
			type: "capture",
			count: 5
		}
	},
	{
		id: "B205",
		tier: "gold",
		descriptionTemplate: "收服本周 UP 妖怪",
		reward: { exp: 120 },
		condition: {
			type: "capture",
			count: 1,
			isUpMonster: true
		}
	},
	{
		id: "B206",
		tier: "gold",
		descriptionTemplate: "触发 1 次赐宝机缘",
		reward: { exp: 80 },
		condition: {
			type: "encounter",
			count: 1
		}
	},
	{
		id: "B207",
		tier: "gold",
		descriptionTemplate: "连续成功 15 次不中断",
		reward: { exp: 100 },
		condition: {
			type: "combo",
			count: 15
		}
	},
	{
		id: "B208",
		tier: "gold",
		descriptionTemplate: "收服 2 只稀有及以上妖怪",
		reward: { exp: 90 },
		condition: {
			type: "capture",
			qualityMin: "rare",
			count: 2
		}
	}
];
const AVAILABLE_PRODUCTS = [
	"aitable",
	"calendar",
	"chat",
	"contact",
	"todo",
	"approval",
	"attendance",
	"report",
	"ding",
	"workbench",
	"devdoc"
];
function hashString(input) {
	return createHash("sha256").update(input).digest().readUInt32BE(0);
}
function seededRandom(seed) {
	let state = seed;
	return () => {
		state = state * 1664525 + 1013904223 & 4294967295;
		return (state >>> 0) / 4294967295;
	};
}
function pickRandom(pool, rng) {
	return pool[Math.floor(rng() * pool.length)];
}
function getDayKey() {
	return new Date((/* @__PURE__ */ new Date()).getTime() + 480 * 60 * 1e3).toISOString().slice(0, 10);
}
/**
* 生成每日悬赏令
*/
function generateDailyBounties(profile) {
	const today = getDayKey();
	if (profile.dailyBounty && profile.dailyBounty.date === today) return profile.dailyBounty;
	const rng = seededRandom(hashString(profile.uidHash + today + "bounty-salt"));
	const state = {
		date: today,
		bounties: [
			pickRandom(BRONZE_POOL, rng),
			pickRandom(SILVER_POOL, rng),
			pickRandom(GOLD_POOL, rng)
		].map((template) => instantiateTemplate(template, rng)),
		completedCount: 0
	};
	profile.dailyBounty = state;
	return state;
}
/**
* 将模板实例化为具体的悬赏令
*/
function instantiateTemplate(template, rng) {
	let description = template.descriptionTemplate;
	const condition = { ...template.condition };
	if (template.hasProductPlaceholder) {
		const product = pickRandom(AVAILABLE_PRODUCTS, rng);
		description = description.replace("{product}", product);
		condition.product = product;
	}
	return {
		id: template.id,
		tier: template.tier,
		description,
		target: condition.count,
		current: 0,
		completed: false,
		reward: { ...template.reward },
		condition
	};
}
const QUALITY_RANK = {
	normal: 0,
	fine: 1,
	rare: 2,
	epic: 3,
	legendary: 4,
	shiny: 5
};
function isQualityAtLeast(actual, minimum) {
	return QUALITY_RANK[actual] >= QUALITY_RANK[minimum];
}
/**
* 操作后更新悬赏令进度
*
* @returns 本次新完成的悬赏令列表
*/
function updateBountyProgress(profile, context) {
	const bountyState = profile.dailyBounty;
	if (!bountyState) return [];
	const today = getDayKey();
	if (bountyState.date !== today) return [];
	const newlyCompleted = [];
	for (const bounty of bountyState.bounties) {
		if (bounty.completed) continue;
		bounty.current;
		updateSingleBountyProgress(bounty, context);
		if (!bounty.completed && bounty.current >= bounty.target) {
			bounty.completed = true;
			bountyState.completedCount += 1;
			newlyCompleted.push(bounty);
			profile.totalExp += bounty.reward.exp;
			profile.bountyHistory.totalCompleted += 1;
			switch (bounty.tier) {
				case "bronze":
					profile.bountyHistory.bronzeCompleted += 1;
					break;
				case "silver":
					profile.bountyHistory.silverCompleted += 1;
					break;
				case "gold":
					profile.bountyHistory.goldCompleted += 1;
					break;
			}
		}
	}
	if (bountyState.completedCount === 3) profile.bountyHistory.consecutiveFullClear += 1;
	return newlyCompleted;
}
function updateSingleBountyProgress(bounty, ctx) {
	const { condition } = bounty;
	switch (condition.type) {
		case "command":
			if (ctx.commandSuccess) if (condition.product) {
				if (ctx.product === condition.product) bounty.current += 1;
			} else bounty.current += 1;
			break;
		case "capture":
			if (ctx.dropResult && !ctx.dropResult.escaped) {
				let matches = true;
				if (condition.qualityMin) matches = matches && isQualityAtLeast(ctx.dropResult.monster.quality, condition.qualityMin);
				if (condition.isUpMonster) matches = matches && ctx.dropResult.isUpMonster;
				if (condition.isNew) matches = matches && ctx.dropResult.isNew;
				if (condition.product) matches = matches && ctx.dropResult.monster.relatedProduct === condition.product;
				if (matches) bounty.current += 1;
			}
			break;
		case "combo":
			bounty.current = Math.min(ctx.currentCombo, bounty.target);
			break;
		case "encounter":
			if (ctx.encounterTriggered) if (bounty.id === "B206") {
				if (ctx.encounterType === "treasure") bounty.current += 1;
			} else bounty.current += 1;
			break;
		case "product_variety":
			bounty.current = Math.min(ctx.todayProducts.size, bounty.target);
			break;
		case "quality_variety":
			bounty.current = Math.min(ctx.todayQualities.size, bounty.target);
			break;
	}
}
/**
* 初始化默认的悬赏历史
*/
function createDefaultBountyHistory() {
	return {
		totalCompleted: 0,
		bronzeCompleted: 0,
		silverCompleted: 0,
		goldCompleted: 0,
		consecutiveFullClear: 0
	};
}
/**
* 检查今日是否需要重置连续全清计数
* （如果昨天没有全部完成，重置为 0）
*/
function checkBountyDayReset(profile) {
	const today = getDayKey();
	if (profile.dailyBounty && profile.dailyBounty.date !== today) {
		if (profile.dailyBounty.completedCount < 3) profile.bountyHistory.consecutiveFullClear = 0;
	}
}
//#endregion
//#region src/game-xiyou/random-event-engine.ts
/**
* 随机事件系统 (v2)
*
* 低概率触发的特殊剧情事件，打破日常节奏，制造惊喜和紧张感。
* 事件分为三类：增益(8%)、挑战(5%)、灾厄(3%)。
* 独立于掉落和机缘触发，同一事件 24 小时内不重复。
*/
function cryptoRandom$3() {
	return randomBytes(4).readUInt32BE(0) / 4294967295;
}
const BLESSING_EVENTS = [
	{
		id: "EV001",
		name: "蟠桃大会",
		category: "blessing",
		triggerRate: .015,
		description: "接下来 10 次操作修行值 ×3",
		flavorText: "王母娘娘设宴，蟠桃大会开席！修行值大涨！",
		effect: {
			type: "exp_multiplier",
			value: 3,
			targetCount: 10
		},
		duration: {
			type: "operation_count",
			total: 10,
			remaining: 10
		}
	},
	{
		id: "EV002",
		name: "月光宝盒",
		category: "blessing",
		triggerRate: .01,
		description: "下一次掉落品质强制提升一级",
		flavorText: "紫霞仙子留下的月光宝盒，时光倒流，命运改写！",
		effect: {
			type: "quality_boost",
			value: 1
		},
		duration: {
			type: "drop_count",
			total: 1,
			remaining: 1
		}
	},
	{
		id: "EV003",
		name: "龙宫寻宝",
		category: "blessing",
		triggerRate: .015,
		description: "立即额外触发一次掉落",
		flavorText: "东海龙宫大门洞开，宝物任你挑选！",
		effect: {
			type: "extra_drop",
			value: 1
		},
		duration: {
			type: "instant",
			total: 1,
			remaining: 0
		}
	},
	{
		id: "EV004",
		name: "仙人指路",
		category: "blessing",
		triggerRate: .02,
		description: "下 5 次操作的产品关联权重 ×5",
		flavorText: "南极仙翁路过，指了指前方：\"那边有好东西。\"",
		effect: {
			type: "product_weight",
			value: 5,
			targetCount: 5
		},
		duration: {
			type: "operation_count",
			total: 5,
			remaining: 5
		}
	},
	{
		id: "EV005",
		name: "蟠桃熟了",
		category: "blessing",
		triggerRate: .01,
		description: "立即获得 30-100 随机修行值",
		flavorText: "三千年一熟的蟠桃，今日恰好落入你手。",
		effect: {
			type: "exp_flat",
			value: 0
		},
		duration: {
			type: "instant",
			total: 1,
			remaining: 0
		}
	},
	{
		id: "EV006",
		name: "土地公的宝箱",
		category: "blessing",
		triggerRate: .01,
		description: "随机获得一件一次性法宝",
		flavorText: "土地公从地下冒出来：\"大圣，这个给你！\"",
		effect: {
			type: "treasure_grant",
			value: 1
		},
		duration: {
			type: "instant",
			total: 1,
			remaining: 0
		}
	}
];
const CHALLENGE_EVENTS_DATA = [
	{
		id: "EV101",
		name: "妖王入侵",
		category: "challenge",
		triggerRate: .015,
		description: "接下来连续成功 5 次",
		flavorText: "一股强大的妖气从远方袭来——\"哈哈哈，齐天大圣不过如此！\"",
		effect: {
			type: "exp_flat",
			value: 0
		},
		duration: {
			type: "operation_count",
			total: 8,
			remaining: 8
		},
		challengeCondition: {
			type: "consecutive_success",
			target: 5,
			current: 0
		},
		successReward: {
			exp: 80,
			pityBonus: 5
		},
		failurePenalty: { expLoss: 30 },
		operationLimit: 8
	},
	{
		id: "EV102",
		name: "火焰山",
		category: "challenge",
		triggerRate: .01,
		description: "接下来 10 次操作中使用 ≥3 种不同产品",
		flavorText: "火焰山烈焰滔天，唯有多方尝试方能通过！",
		effect: {
			type: "exp_flat",
			value: 0
		},
		duration: {
			type: "operation_count",
			total: 10,
			remaining: 10
		},
		challengeCondition: {
			type: "product_variety",
			target: 3,
			current: 0
		},
		successReward: {
			exp: 60,
			escapeRateMod: -.05
		},
		failurePenalty: {
			expLoss: 0,
			comboReset: true
		},
		operationLimit: 10
	},
	{
		id: "EV103",
		name: "通天河阻路",
		category: "challenge",
		triggerRate: .01,
		description: "接下来连续成功 3 次且收服 ≥1 只妖怪",
		flavorText: "通天河水势汹涌，需要勇气和实力才能渡过！",
		effect: {
			type: "exp_flat",
			value: 0
		},
		duration: {
			type: "operation_count",
			total: 5,
			remaining: 5
		},
		challengeCondition: {
			type: "consecutive_success",
			target: 3,
			current: 0
		},
		successReward: {
			exp: 100,
			extraDrop: true
		},
		failurePenalty: { expLoss: 20 },
		operationLimit: 5
	},
	{
		id: "EV104",
		name: "真假美猴王",
		category: "challenge",
		triggerRate: .005,
		description: "接下来 3 次掉落中选出\"真\"的那只",
		flavorText: "六耳猕猴现身，真假难辨！",
		effect: {
			type: "exp_flat",
			value: 0
		},
		duration: {
			type: "drop_count",
			total: 3,
			remaining: 3
		},
		challengeCondition: {
			type: "pick_correct",
			target: 1,
			current: 0
		},
		successReward: { exp: 100 },
		failurePenalty: { expLoss: 0 },
		operationLimit: 3
	},
	{
		id: "EV105",
		name: "盘丝洞迷阵",
		category: "challenge",
		triggerRate: .005,
		description: "接下来 5 次操作必须使用 5 种不同产品",
		flavorText: "蜘蛛精的丝网密布，每一步都不能重复！",
		effect: {
			type: "exp_flat",
			value: 0
		},
		duration: {
			type: "operation_count",
			total: 5,
			remaining: 5
		},
		challengeCondition: {
			type: "product_variety",
			target: 5,
			current: 0
		},
		successReward: {
			exp: 120,
			monster: { qualityMin: "rare" }
		},
		failurePenalty: { expLoss: 50 },
		operationLimit: 5
	},
	{
		id: "EV106",
		name: "比丘国救童",
		category: "challenge",
		triggerRate: .005,
		description: "接下来 8 次操作中成功率 ≥80%",
		flavorText: "比丘国的孩子们需要你的帮助！",
		effect: {
			type: "exp_flat",
			value: 0
		},
		duration: {
			type: "operation_count",
			total: 8,
			remaining: 8
		},
		challengeCondition: {
			type: "success_rate",
			target: 7,
			current: 0
		},
		successReward: {
			exp: 150,
			treasureFragment: "random"
		},
		failurePenalty: { expLoss: 40 },
		operationLimit: 8
	}
];
const DISASTER_EVENTS = [
	{
		id: "EV201",
		name: "黑风来袭",
		category: "disaster",
		triggerRate: .01,
		description: "接下来 5 次掉落逃跑率 +20%",
		flavorText: "黑风山的妖气蔓延而来——\"嘿嘿嘿，让你的妖怪都跑光！\"",
		effect: {
			type: "escape_rate_mod",
			value: .2
		},
		duration: {
			type: "drop_count",
			total: 5,
			remaining: 5
		},
		resolution: {
			type: "consecutive_success",
			count: 3,
			description: "连续成功 3 次可提前解除"
		}
	},
	{
		id: "EV202",
		name: "金蝉脱壳",
		category: "disaster",
		triggerRate: .005,
		description: "随机一只已收服的精良妖怪逃跑",
		flavorText: "一阵妖风吹过，你的妖怪图鉴闪了一下……",
		effect: {
			type: "monster_escape",
			value: 1
		},
		duration: {
			type: "instant",
			total: 1,
			remaining: 0
		}
	},
	{
		id: "EV203",
		name: "妖雾弥漫",
		category: "disaster",
		triggerRate: .008,
		description: "接下来 3 次掉落品质上限降为精良",
		flavorText: "浓雾笼罩，视线模糊，只能看到近处的小妖……",
		effect: {
			type: "quality_cap",
			value: 1
		},
		duration: {
			type: "drop_count",
			total: 3,
			remaining: 3
		},
		resolution: {
			type: "use_treasure",
			treasureId: "zhaoyaojing",
			description: "使用法宝\"照妖镜\"可立即解除"
		}
	},
	{
		id: "EV204",
		name: "紧箍咒发作",
		category: "disaster",
		triggerRate: .004,
		description: "接下来 5 次操作修行值减半",
		flavorText: "头痛欲裂！唐僧又念紧箍咒了！",
		effect: {
			type: "exp_halve",
			value: .5
		},
		duration: {
			type: "operation_count",
			total: 5,
			remaining: 5
		},
		resolution: {
			type: "complete_bounty",
			description: "完成 1 张悬赏令可提前解除"
		}
	},
	{
		id: "EV205",
		name: "五行山镇压",
		category: "disaster",
		triggerRate: .002,
		description: "连击归零 + 接下来 3 次操作无掉落",
		flavorText: "五行山从天而降，压得你动弹不得！",
		effect: {
			type: "no_drop",
			value: 3
		},
		duration: {
			type: "operation_count",
			total: 3,
			remaining: 3
		},
		resolution: {
			type: "trigger_encounter",
			description: "触发 1 次神仙机缘可提前解除"
		}
	},
	{
		id: "EV206",
		name: "走火入魔",
		category: "disaster",
		triggerRate: .001,
		description: "修行值 -100 + 保底计数器全部 -10",
		flavorText: "修炼走火入魔，功力大损！",
		effect: {
			type: "exp_loss",
			value: 100
		},
		duration: {
			type: "instant",
			total: 1,
			remaining: 0
		}
	}
];
/**
* 创建默认的活跃事件状态
*/
function createDefaultActiveEventState() {
	return {
		currentEvents: [],
		activeChallenge: null,
		lastEventTriggerTime: {}
	};
}
/**
* 创建默认的事件统计
*/
function createDefaultEventStats() {
	return {
		totalTriggered: 0,
		challengesCompleted: 0,
		challengesFailed: 0,
		disastersResolved: 0
	};
}
/**
* 检查并触发随机事件
*
* @returns 触发的事件，或 null
*/
function checkRandomEvent(profile) {
	const now = Date.now();
	const oneDayMs = 1440 * 60 * 1e3;
	const candidates = [
		...BLESSING_EVENTS,
		...CHALLENGE_EVENTS_DATA,
		...DISASTER_EVENTS
	];
	for (const candidate of candidates) {
		if (now - (profile.activeEvents.lastEventTriggerTime[candidate.id] ?? 0) < oneDayMs) continue;
		if (candidate.category === "challenge" && profile.activeEvents.activeChallenge) continue;
		if (cryptoRandom$3() < candidate.triggerRate) {
			profile.activeEvents.lastEventTriggerTime[candidate.id] = now;
			profile.eventStats.totalTriggered += 1;
			const event = instantiateEvent(candidate, profile);
			if (event.category === "challenge") profile.activeEvents.activeChallenge = event;
			else if (event.duration.type !== "instant") profile.activeEvents.currentEvents.push(event);
			profile.eventHistory.push({
				eventId: event.id,
				triggeredAt: now
			});
			return event;
		}
	}
	return null;
}
/** 一次性法宝 ID 池（用于 EV006 土地公的宝箱） */
const CONSUMABLE_TREASURE_IDS = ["pantao", "renshenguo"];
/**
* 实例化事件（处理随机值、即时效果等）
*
* 即时事件的效果在此函数中直接应用到 profile。
* 持续性事件仅初始化状态，效果由 tickActiveEvents / 查询函数处理。
*/
function instantiateEvent(template, profile) {
	const event = JSON.parse(JSON.stringify(template));
	switch (event.id) {
		case "EV005": {
			const expGain = Math.floor(30 + cryptoRandom$3() * 71);
			event.effect.value = expGain;
			profile.totalExp += expGain;
			break;
		}
		case "EV006": {
			const treasureId = CONSUMABLE_TREASURE_IDS[Math.floor(cryptoRandom$3() * CONSUMABLE_TREASURE_IDS.length)];
			event.effect.value = 1;
			if (!profile.treasures.includes(treasureId)) profile.treasures.push(treasureId);
			event.description = `获得了一次性法宝：${treasureId === "pantao" ? "蟠桃" : "人参果"}`;
			break;
		}
		case "EV202":
			event.effect.value = 1;
			break;
		case "EV205":
			profile.currentCombo = 0;
			break;
		case "EV206":
			profile.totalExp = Math.max(0, profile.totalExp - 100);
			profile.pityCounters.sinceLastRare = Math.max(0, profile.pityCounters.sinceLastRare - 10);
			profile.pityCounters.sinceLastEpic = Math.max(0, profile.pityCounters.sinceLastEpic - 10);
			profile.pityCounters.sinceLastLegendary = Math.max(0, profile.pityCounters.sinceLastLegendary - 10);
			profile.pityCounters.totalDropsWithoutShiny = Math.max(0, profile.pityCounters.totalDropsWithoutShiny - 10);
			break;
	}
	if (event.category === "challenge") {
		const challengeEvent = event;
		challengeEvent.progress = {
			operationsUsed: 0,
			operationLimit: challengeEvent.operationLimit,
			conditionMet: false,
			usedProducts: []
		};
	}
	return event;
}
/**
* 每次操作后更新活跃事件的持续时间和状态
*
* @returns 本次过期/完成的事件列表
*/
function tickActiveEvents(profile, operationSuccess, product, capturedMonster) {
	const results = [];
	const remainingEvents = [];
	for (const event of profile.activeEvents.currentEvents) {
		if (event.duration.type === "operation_count") event.duration.remaining -= 1;
		if (event.category === "disaster" && event.resolution) {
			if (checkResolution(event.resolution, profile, operationSuccess)) {
				results.push({
					event,
					outcome: "resolved"
				});
				profile.eventStats.disastersResolved += 1;
				updateEventHistory(profile, event.id, "resolved");
				continue;
			}
		}
		if (event.duration.remaining <= 0) {
			results.push({
				event,
				outcome: "expired"
			});
			updateEventHistory(profile, event.id, "expired");
		} else remainingEvents.push(event);
	}
	profile.activeEvents.currentEvents = remainingEvents;
	const challenge = profile.activeEvents.activeChallenge;
	if (challenge) {
		challenge.progress.operationsUsed += 1;
		challenge.duration.remaining -= 1;
		updateChallengeProgress(challenge, operationSuccess, product, capturedMonster);
		if (challenge.progress.conditionMet) {
			results.push({
				event: challenge,
				outcome: "success"
			});
			applyChallengeReward(profile, challenge);
			profile.eventStats.challengesCompleted += 1;
			updateEventHistory(profile, challenge.id, "success");
			profile.activeEvents.activeChallenge = null;
		} else if (challenge.progress.operationsUsed >= challenge.progress.operationLimit) {
			results.push({
				event: challenge,
				outcome: "failure"
			});
			applyChallengePenalty(profile, challenge);
			profile.eventStats.challengesFailed += 1;
			updateEventHistory(profile, challenge.id, "failure");
			profile.activeEvents.activeChallenge = null;
		}
	}
	return results;
}
/**
* 掉落时递减 drop_count 类型事件的剩余次数
*/
function tickDropEvents(profile) {
	for (const event of profile.activeEvents.currentEvents) if (event.duration.type === "drop_count") event.duration.remaining -= 1;
}
/**
* 获取当前活跃的修行值倍率修正
*/
function getActiveExpMultiplier(profile) {
	let multiplier = 1;
	for (const event of profile.activeEvents.currentEvents) {
		if (event.effect.type === "exp_multiplier") multiplier *= event.effect.value;
		if (event.effect.type === "exp_halve") multiplier *= event.effect.value;
	}
	return multiplier;
}
/**
* 检查是否有品质提升事件
*/
function getQualityBoost(profile) {
	for (const event of profile.activeEvents.currentEvents) if (event.effect.type === "quality_boost" && event.duration.remaining > 0) return event.effect.value;
	return 0;
}
/**
* 检查是否有品质上限事件
*/
function getQualityCap(profile) {
	for (const event of profile.activeEvents.currentEvents) if (event.effect.type === "quality_cap" && event.duration.remaining > 0) return "fine";
	return null;
}
/**
* 检查是否有禁止掉落事件
*/
function isDropSuppressed(profile) {
	return profile.activeEvents.currentEvents.some((e) => e.effect.type === "no_drop" && e.duration.remaining > 0);
}
function checkResolution(resolution, profile, operationSuccess) {
	switch (resolution.type) {
		case "consecutive_success": return profile.currentCombo >= (resolution.count ?? 3);
		case "use_treasure": return false;
		case "complete_bounty": return false;
		case "trigger_encounter": return false;
		default: return false;
	}
}
/**
* 手动解除灾厄事件（由外部系统调用）
*/
function resolveDisasterEvent(profile, resolutionType) {
	const index = profile.activeEvents.currentEvents.findIndex((e) => e.category === "disaster" && e.resolution?.type === resolutionType);
	if (index === -1) return null;
	const event = profile.activeEvents.currentEvents[index];
	profile.activeEvents.currentEvents.splice(index, 1);
	profile.eventStats.disastersResolved += 1;
	updateEventHistory(profile, event.id, "resolved");
	return event;
}
function updateChallengeProgress(challenge, operationSuccess, product, capturedMonster) {
	const usedProducts = challenge.progress.usedProducts ?? [];
	switch (challenge.challengeCondition.type) {
		case "consecutive_success":
			if (operationSuccess) challenge.challengeCondition.current += 1;
			else challenge.challengeCondition.current = 0;
			break;
		case "product_variety":
			if (!usedProducts.includes(product)) {
				usedProducts.push(product);
				challenge.progress.usedProducts = usedProducts;
			}
			challenge.challengeCondition.current = usedProducts.length;
			break;
		case "success_rate":
			if (operationSuccess) challenge.challengeCondition.current += 1;
			break;
		case "capture_count":
			if (capturedMonster) challenge.challengeCondition.current += 1;
			break;
		case "pick_correct":
			if (cryptoRandom$3() < 1 / 3) challenge.challengeCondition.current += 1;
			break;
	}
	if (challenge.challengeCondition.current >= challenge.challengeCondition.target) challenge.progress.conditionMet = true;
}
function applyChallengeReward(profile, challenge) {
	const reward = challenge.successReward;
	profile.totalExp += reward.exp;
	if (reward.pityBonus) {
		profile.pityCounters.sinceLastRare += reward.pityBonus;
		profile.pityCounters.sinceLastEpic += reward.pityBonus;
		profile.pityCounters.sinceLastLegendary += reward.pityBonus;
	}
}
function applyChallengePenalty(profile, challenge) {
	const penalty = challenge.failurePenalty;
	profile.totalExp = Math.max(0, profile.totalExp - penalty.expLoss);
	if (penalty.comboReset) profile.currentCombo = 0;
	if (penalty.pityLoss) {
		profile.pityCounters.sinceLastRare = Math.max(0, profile.pityCounters.sinceLastRare - penalty.pityLoss);
		profile.pityCounters.sinceLastEpic = Math.max(0, profile.pityCounters.sinceLastEpic - penalty.pityLoss);
		profile.pityCounters.sinceLastLegendary = Math.max(0, profile.pityCounters.sinceLastLegendary - penalty.pityLoss);
	}
}
function updateEventHistory(profile, eventId, outcome) {
	const entry = profile.eventHistory.find((e) => e.eventId === eventId && !e.outcome);
	if (entry) entry.outcome = outcome;
}
//#endregion
//#region src/game-xiyou/storage.ts
/**
* JSON 持久化层
*
* 所有养成数据存储在 ~/.dingtalk-connector/gamification/ 目录下，
* 按 UID 哈希分文件存储，支持 profile / collection / history 三类数据。
*/
const STORAGE_DIR = path.join(os.homedir(), ".dingtalk-connector", "gamification");
const CHECKSUM_SECRET = "xiyou-hmac-secret-2026";
function ensureStorageDir() {
	if (!fs.existsSync(STORAGE_DIR)) fs.mkdirSync(STORAGE_DIR, { recursive: true });
}
function getProfilePath(uidHash) {
	return path.join(STORAGE_DIR, `profile-${uidHash}.json`);
}
function getCollectionPath(uidHash) {
	return path.join(STORAGE_DIR, `collection-${uidHash}.json`);
}
function getHistoryPath(uidHash) {
	return path.join(STORAGE_DIR, `history-${uidHash}.json`);
}
function computeChecksum(profile) {
	const payload = `${profile.uidHash}:${profile.totalExp}:${profile.level}:${profile.totalOperations}`;
	return createHmac("sha256", CHECKSUM_SECRET).update(payload).digest("hex").slice(0, 32);
}
function createDefaultProfile(uidHash) {
	const profile = {
		uidHash,
		level: 1,
		title: "凡人",
		totalExp: 0,
		totalOperations: 0,
		currentCombo: 0,
		maxCombo: 0,
		consecutiveSignInDays: 0,
		lastSignInDate: "",
		totalRecoveries: 0,
		consecutiveFailures: 0,
		productUsage: {},
		pityCounters: {
			sinceLastRare: 0,
			sinceLastEpic: 0,
			sinceLastLegendary: 0,
			totalDropsWithoutShiny: 0
		},
		buffs: [],
		settings: {
			enabled: false,
			showDropAnimation: true,
			muteNormalDrops: false
		},
		encounters: [],
		unlockedAchievements: [],
		treasures: [],
		consumedTreasures: [],
		createdAt: Date.now(),
		escapeHistory: {},
		totalEscapes: 0,
		dailyBounty: null,
		bountyHistory: createDefaultBountyHistory(),
		activeEvents: createDefaultActiveEventState(),
		eventStats: createDefaultEventStats(),
		eventHistory: []
	};
	return {
		...profile,
		checksum: computeChecksum(profile)
	};
}
function loadProfile(uidHash) {
	ensureStorageDir();
	const filePath = getProfilePath(uidHash);
	if (!fs.existsSync(filePath)) {
		const profile = createDefaultProfile(uidHash);
		saveProfile(profile);
		return profile;
	}
	try {
		const raw = fs.readFileSync(filePath, "utf-8");
		return migrateProfile(JSON.parse(raw));
	} catch {
		const profile = createDefaultProfile(uidHash);
		saveProfile(profile);
		return profile;
	}
}
/**
* 补全旧版本 profile 中缺失的 v2 字段，确保向后兼容
*/
function migrateProfile(profile) {
	let migrated = false;
	if (!profile.escapeHistory) {
		profile.escapeHistory = {};
		migrated = true;
	}
	if (profile.totalEscapes == null) {
		profile.totalEscapes = 0;
		migrated = true;
	}
	if (profile.dailyBounty === void 0) {
		profile.dailyBounty = null;
		migrated = true;
	}
	if (!profile.bountyHistory) {
		profile.bountyHistory = createDefaultBountyHistory();
		migrated = true;
	}
	if (!profile.activeEvents) {
		profile.activeEvents = createDefaultActiveEventState();
		migrated = true;
	}
	if (!profile.eventStats) {
		profile.eventStats = createDefaultEventStats();
		migrated = true;
	}
	if (!profile.eventHistory) {
		profile.eventHistory = [];
		migrated = true;
	}
	if (migrated) saveProfile(profile);
	return profile;
}
function saveProfile(profile) {
	ensureStorageDir();
	const withChecksum = {
		...profile,
		checksum: computeChecksum(profile)
	};
	const filePath = getProfilePath(profile.uidHash);
	fs.writeFileSync(filePath, JSON.stringify(withChecksum, null, 2), "utf-8");
}
function createDefaultCollection(uidHash) {
	return {
		uidHash,
		entries: []
	};
}
function loadCollection(uidHash) {
	ensureStorageDir();
	const filePath = getCollectionPath(uidHash);
	if (!fs.existsSync(filePath)) {
		const collection = createDefaultCollection(uidHash);
		saveCollection(collection);
		return collection;
	}
	try {
		const raw = fs.readFileSync(filePath, "utf-8");
		return JSON.parse(raw);
	} catch {
		const collection = createDefaultCollection(uidHash);
		saveCollection(collection);
		return collection;
	}
}
function saveCollection(collection) {
	ensureStorageDir();
	const filePath = getCollectionPath(collection.uidHash);
	fs.writeFileSync(filePath, JSON.stringify(collection, null, 2), "utf-8");
}
const MAX_HISTORY_RECORDS = 500;
function createDefaultHistory(uidHash) {
	return {
		uidHash,
		records: []
	};
}
function loadHistory(uidHash) {
	ensureStorageDir();
	const filePath = getHistoryPath(uidHash);
	if (!fs.existsSync(filePath)) return createDefaultHistory(uidHash);
	try {
		const raw = fs.readFileSync(filePath, "utf-8");
		return JSON.parse(raw);
	} catch {
		return createDefaultHistory(uidHash);
	}
}
function saveHistory(history) {
	ensureStorageDir();
	if (history.records.length > MAX_HISTORY_RECORDS) history.records = history.records.slice(-MAX_HISTORY_RECORDS);
	const filePath = getHistoryPath(history.uidHash);
	fs.writeFileSync(filePath, JSON.stringify(history, null, 2), "utf-8");
}
//#endregion
//#region src/game-xiyou/types.ts
const QUALITY_LABELS = {
	normal: "⬜ 普通",
	fine: "🟢 精良",
	rare: "🔵 稀有",
	epic: "🟣 史诗",
	legendary: "🟡 传说",
	shiny: "✨ 闪光"
};
const QUALITY_ORDER = [
	"normal",
	"fine",
	"rare",
	"epic",
	"legendary",
	"shiny"
];
const LEVEL_DEFINITIONS = [
	{
		level: 1,
		title: "凡人",
		requiredExp: 0,
		unlockDescription: "基础掉落池"
	},
	{
		level: 2,
		title: "樵夫",
		requiredExp: 120
	},
	{
		level: 3,
		title: "修行者",
		requiredExp: 320,
		unlockDescription: "解锁\"机缘\"系统（神仙随机现身）"
	},
	{
		level: 4,
		title: "散仙",
		requiredExp: 800,
		unlockDescription: "掉落池扩展：加入稀有妖怪"
	},
	{
		level: 5,
		title: "天兵",
		requiredExp: 2e3,
		unlockDescription: "解锁\"法宝\"系统"
	},
	{
		level: 6,
		title: "天将",
		requiredExp: 4e3,
		unlockDescription: "掉落池扩展：加入史诗妖怪"
	},
	{
		level: 7,
		title: "哪吒",
		requiredExp: 8e3,
		unlockDescription: "连击加成上限提升至 ×4.0"
	},
	{
		level: 8,
		title: "二郎神",
		requiredExp: 16e3,
		unlockDescription: "掉落池扩展：加入传说妖怪"
	},
	{
		level: 9,
		title: "齐天大圣",
		requiredExp: 32e3,
		unlockDescription: "解锁\"闪光\"掉落"
	},
	{
		level: 10,
		title: "斗战胜佛",
		requiredExp: 6e4,
		unlockDescription: "全图鉴解锁提示、专属称号色"
	}
];
const PRODUCT_BASE_EXP = {
	aitable: 3,
	calendar: 2,
	chat: 2,
	contact: 1,
	todo: 2,
	approval: 4,
	attendance: 2,
	report: 3,
	ding: 1,
	workbench: 3,
	devdoc: 1
};
/** v2: 保底阈值上调 */
const PITY_THRESHOLDS = {
	rare: 30,
	epic: 80,
	legendary: 150,
	shiny: 800
};
/** v2: 软保底起始点 — 接近硬保底时概率逐步提升 */
const SOFT_PITY_START = {
	rare: 20,
	epic: 60,
	legendary: 120,
	shiny: 600
};
/** v2: 软保底每次额外增加的概率 */
const SOFT_PITY_RATE_PER_STEP = {
	rare: .03,
	epic: .02,
	legendary: .01,
	shiny: 5e-4
};
/** 各品质的基础逃跑率 */
const BASE_ESCAPE_RATES = {
	normal: 0,
	fine: .1,
	rare: .25,
	epic: .4,
	legendary: .6,
	shiny: .75
};
/** 逃跑率的最低下限 */
const MIN_ESCAPE_RATE = .05;
const DROP_RATES = {
	shiny: .001,
	legendary: .009,
	epic: .04,
	rare: .1,
	fine: .25,
	normal: .6
};
/** 等级门槛：低于此等级的品质会降级 */
const QUALITY_LEVEL_GATES = {
	rare: 4,
	epic: 6,
	legendary: 8,
	shiny: 9
};
/** 连击加成倍率 */
const COMBO_MULTIPLIERS = [
	{
		threshold: 10,
		multiplier: 3
	},
	{
		threshold: 5,
		multiplier: 2
	},
	{
		threshold: 3,
		multiplier: 1.5
	}
];
/** 机缘触发概率 */
const ENCOUNTER_RATES = {
	guidance: .08,
	treasure: .03,
	apprentice: .005
};
//#endregion
//#region src/game-xiyou/exp-calculator.ts
/**
* 获取产品的基础修行值
*/
function getBaseExp(product) {
	return PRODUCT_BASE_EXP[product] ?? 2;
}
/**
* 计算连击加成倍率
*/
function getComboMultiplier(comboCount, buffs) {
	const comboLimitBonus = buffs.filter((b) => b.effect === "comboLimitBonus").reduce((sum, b) => sum + b.value, 0);
	const comboBonusFromBuffs = buffs.filter((b) => b.effect === "comboBonus").reduce((sum, b) => sum + b.value, 0);
	let baseMultiplier = 1;
	for (const { threshold, multiplier } of COMBO_MULTIPLIERS) if (comboCount >= threshold) {
		baseMultiplier = multiplier;
		break;
	}
	if (comboLimitBonus > 0 && comboCount >= 10) baseMultiplier = Math.min(baseMultiplier + comboLimitBonus, 5);
	return baseMultiplier + comboBonusFromBuffs;
}
/**
* 计算首次使用加成
*/
function getFirstUseMultiplier(product, productUsage) {
	return (productUsage[product] ?? 0) === 0 ? 5 : 1;
}
/**
* 计算签到奖励
*/
function getSignInBonus(profile) {
	const today = (/* @__PURE__ */ new Date()).toISOString().slice(0, 10);
	if (profile.lastSignInDate === today) return 0;
	return 10;
}
/**
* 计算连续签到奖励
*/
function getConsecutiveSignInBonus(profile, buffs) {
	const today = (/* @__PURE__ */ new Date()).toISOString().slice(0, 10);
	if (profile.lastSignInDate === today) return 0;
	const signInMultiplier = buffs.filter((b) => b.effect === "signInMultiplier").reduce((max, b) => Math.max(max, b.value), 1);
	const consecutiveDays = profile.consecutiveSignInDays + 1;
	const bonus = Math.min(consecutiveDays * 2, 30);
	return Math.floor(bonus * signInMultiplier);
}
/**
* 计算 buff 总倍率
*/
function getBuffMultiplier(buffs) {
	return buffs.filter((b) => b.effect === "expMultiplier").reduce((multiplier, b) => multiplier * b.value, 1);
}
/**
* 计算一次操作获得的总修行值
*/
function calculateExp(product, profile) {
	const baseExp = getBaseExp(product);
	const comboMultiplier = getComboMultiplier(profile.currentCombo + 1, profile.buffs);
	const firstUseMultiplier = getFirstUseMultiplier(product, profile.productUsage);
	const signInBonus = getSignInBonus(profile);
	const consecutiveSignInBonus = getConsecutiveSignInBonus(profile, profile.buffs);
	const buffMultiplier = getBuffMultiplier(profile.buffs);
	return {
		baseExp,
		comboMultiplier,
		firstUseMultiplier,
		signInBonus,
		consecutiveSignInBonus,
		buffMultiplier,
		totalExp: Math.floor((baseExp * comboMultiplier * firstUseMultiplier + signInBonus + consecutiveSignInBonus) * buffMultiplier)
	};
}
/**
* 更新签到状态
*/
function updateSignInStatus(profile) {
	const today = (/* @__PURE__ */ new Date()).toISOString().slice(0, 10);
	if (profile.lastSignInDate === today) return;
	const yesterday = (/* @__PURE__ */ new Date(Date.now() - 864e5)).toISOString().slice(0, 10);
	if (profile.lastSignInDate === yesterday) profile.consecutiveSignInDays += 1;
	else profile.consecutiveSignInDays = 1;
	profile.lastSignInDate = today;
}
//#endregion
//#region src/game-xiyou/level-system.ts
/**
* 根据累计修行值计算当前等级
*/
function calculateLevel(totalExp) {
	let currentLevel = LEVEL_DEFINITIONS[0];
	for (const levelDef of LEVEL_DEFINITIONS) if (totalExp >= levelDef.requiredExp) currentLevel = levelDef;
	else break;
	return currentLevel;
}
/**
* 获取下一级的定义（如果已满级则返回 null）
*/
function getNextLevel(currentLevel) {
	const nextIndex = LEVEL_DEFINITIONS.findIndex((l) => l.level === currentLevel) + 1;
	if (nextIndex >= LEVEL_DEFINITIONS.length) return null;
	return LEVEL_DEFINITIONS[nextIndex];
}
/**
* 计算距离下一级还需要多少修行值
*/
function getExpToNextLevel(totalExp) {
	const nextLevel = getNextLevel(calculateLevel(totalExp).level);
	if (!nextLevel) return null;
	return nextLevel.requiredExp - totalExp;
}
/**
* 获取当前等级的进度百分比
*/
function getLevelProgress(totalExp) {
	const currentLevel = calculateLevel(totalExp);
	const nextLevel = getNextLevel(currentLevel.level);
	if (!nextLevel) return 100;
	const levelRange = nextLevel.requiredExp - currentLevel.requiredExp;
	const currentProgress = totalExp - currentLevel.requiredExp;
	return Math.floor(currentProgress / levelRange * 100);
}
/**
* 检查是否发生升级，返回升级结果
*/
function checkLevelUp(profile, expGained) {
	const previousLevel = calculateLevel(profile.totalExp);
	const newLevel = calculateLevel(profile.totalExp + expGained);
	if (newLevel.level <= previousLevel.level) return null;
	return {
		previousLevel: previousLevel.level,
		previousTitle: previousLevel.title,
		newLevel: newLevel.level,
		newTitle: newLevel.title,
		unlockDescription: newLevel.unlockDescription
	};
}
/**
* 应用升级到 profile
*/
function applyLevelUp(profile) {
	const levelDef = calculateLevel(profile.totalExp);
	profile.level = levelDef.level;
	profile.title = levelDef.title;
}
//#endregion
//#region src/game-xiyou/pity-counter.ts
/**
* 检查是否触发硬保底，返回应强制掉落的品质（如果有）
*/
function checkPityTrigger(counters) {
	if (counters.totalDropsWithoutShiny >= PITY_THRESHOLDS.shiny) return "shiny";
	if (counters.sinceLastLegendary >= PITY_THRESHOLDS.legendary) return "legendary";
	if (counters.sinceLastEpic >= PITY_THRESHOLDS.epic) return "epic";
	if (counters.sinceLastRare >= PITY_THRESHOLDS.rare) return "rare";
	return null;
}
/**
* v2: 计算软保底额外概率加成
*
* 在接近硬保底阈值时，对应品质的掉落概率逐步提升，
* 避免"临门一脚"的漫长等待。
*
* @returns 各品质的额外概率加成 { rare: 0.06, epic: 0, ... }
*/
function getSoftPityBonuses(counters) {
	const bonuses = {};
	if (counters.sinceLastRare >= SOFT_PITY_START.rare) bonuses.rare = (counters.sinceLastRare - SOFT_PITY_START.rare) * SOFT_PITY_RATE_PER_STEP.rare;
	if (counters.sinceLastEpic >= SOFT_PITY_START.epic) bonuses.epic = (counters.sinceLastEpic - SOFT_PITY_START.epic) * SOFT_PITY_RATE_PER_STEP.epic;
	if (counters.sinceLastLegendary >= SOFT_PITY_START.legendary) bonuses.legendary = (counters.sinceLastLegendary - SOFT_PITY_START.legendary) * SOFT_PITY_RATE_PER_STEP.legendary;
	if (counters.totalDropsWithoutShiny >= SOFT_PITY_START.shiny) bonuses.shiny = (counters.totalDropsWithoutShiny - SOFT_PITY_START.shiny) * SOFT_PITY_RATE_PER_STEP.shiny;
	return bonuses;
}
/**
* 更新保底计数器
*
* 掉落后递增所有计数器，然后重置对应品质及以下的计数器
*/
function updatePityCounters(counters, droppedQuality, isShiny) {
	counters.sinceLastRare += 1;
	counters.sinceLastEpic += 1;
	counters.sinceLastLegendary += 1;
	counters.totalDropsWithoutShiny += 1;
	const qualityIndex = QUALITY_ORDER.indexOf(droppedQuality);
	if (isShiny || droppedQuality === "shiny") counters.totalDropsWithoutShiny = 0;
	if (qualityIndex >= QUALITY_ORDER.indexOf("legendary")) counters.sinceLastLegendary = 0;
	if (qualityIndex >= QUALITY_ORDER.indexOf("epic")) counters.sinceLastEpic = 0;
	if (qualityIndex >= QUALITY_ORDER.indexOf("rare")) counters.sinceLastRare = 0;
}
//#endregion
//#region src/game-xiyou/monster-pool.ts
/**
* 妖怪数据（内联，避免运行时文件系统依赖）
*/
const allMonsters = [
	{
		id: "N001",
		name: "巡山小妖",
		quality: "normal",
		origin: "各山洞",
		relatedProduct: null,
		captureQuote: "大王叫我来巡山～"
	},
	{
		id: "N002",
		name: "树精",
		quality: "normal",
		origin: "荆棘岭",
		relatedProduct: "contact",
		captureQuote: "落叶归根，不过如此。"
	},
	{
		id: "N003",
		name: "草头神",
		quality: "normal",
		origin: "通天河畔",
		relatedProduct: "calendar",
		captureQuote: "时辰到了，该走了。"
	},
	{
		id: "N004",
		name: "虾兵",
		quality: "normal",
		origin: "东海",
		relatedProduct: "chat",
		captureQuote: "龙宫不是你想来就能来的！"
	},
	{
		id: "N005",
		name: "蟹将",
		quality: "normal",
		origin: "东海",
		relatedProduct: "chat",
		captureQuote: "横行霸道？那是我的专利。"
	},
	{
		id: "N006",
		name: "山神",
		quality: "normal",
		origin: "各处",
		relatedProduct: "attendance",
		captureQuote: "此山是我开，此树是我栽。"
	},
	{
		id: "N007",
		name: "土地公",
		quality: "normal",
		origin: "各处",
		relatedProduct: "contact",
		captureQuote: "大圣饶命，小神知无不言。"
	},
	{
		id: "N008",
		name: "夜叉",
		quality: "normal",
		origin: "水府",
		relatedProduct: "ding",
		captureQuote: "水底的消息，最快。"
	},
	{
		id: "N009",
		name: "狼妖",
		quality: "normal",
		origin: "黄风岭",
		relatedProduct: "todo",
		captureQuote: "待办事项？我只待吃人。"
	},
	{
		id: "N010",
		name: "蛇妖",
		quality: "normal",
		origin: "蛇盘山",
		relatedProduct: "devdoc",
		captureQuote: "嘶——文档里藏着秘密。"
	},
	{
		id: "N011",
		name: "鹿精",
		quality: "normal",
		origin: "比丘国",
		relatedProduct: "report",
		captureQuote: "今日份的鹿茸报告。"
	},
	{
		id: "N012",
		name: "兔精",
		quality: "normal",
		origin: "天竺国",
		relatedProduct: "calendar",
		captureQuote: "月宫的日程，排得满满的。"
	},
	{
		id: "N013",
		name: "鱼精",
		quality: "normal",
		origin: "通天河",
		relatedProduct: "aitable",
		captureQuote: "河底的账本，一条不差。"
	},
	{
		id: "N014",
		name: "龟精",
		quality: "normal",
		origin: "通天河",
		relatedProduct: "todo",
		captureQuote: "慢是慢了点，但待办一定完成。"
	},
	{
		id: "N015",
		name: "猪妖",
		quality: "normal",
		origin: "福陵山",
		relatedProduct: "report",
		captureQuote: "日报？让我先睡一觉再说。"
	},
	{
		id: "N016",
		name: "鸡精",
		quality: "normal",
		origin: "毒敌山",
		relatedProduct: "attendance",
		captureQuote: "打鸣就是打卡，准时得很。"
	},
	{
		id: "N017",
		name: "鼠精",
		quality: "normal",
		origin: "无底洞",
		relatedProduct: "aitable",
		captureQuote: "数据？我最擅长搬运了。"
	},
	{
		id: "N018",
		name: "蝙蝠精",
		quality: "normal",
		origin: "黄花观",
		relatedProduct: "ding",
		captureQuote: "暗夜传信，无声无息。"
	},
	{
		id: "N019",
		name: "石妖",
		quality: "normal",
		origin: "花果山",
		relatedProduct: "workbench",
		captureQuote: "石头里蹦出来的，不止猴子。"
	},
	{
		id: "N020",
		name: "柳树精",
		quality: "normal",
		origin: "荆棘岭",
		relatedProduct: "approval",
		captureQuote: "柳条一挥，审批盖章。"
	},
	{
		id: "R001",
		name: "黑风怪",
		quality: "fine",
		origin: "黑风山",
		relatedProduct: "workbench",
		captureQuote: "这袈裟，归我了！"
	},
	{
		id: "R002",
		name: "黄风怪",
		quality: "fine",
		origin: "黄风岭",
		relatedProduct: "chat",
		captureQuote: "三昧神风，吹！"
	},
	{
		id: "R003",
		name: "白骨精",
		quality: "fine",
		origin: "白虎岭",
		relatedProduct: "contact",
		captureQuote: "变化之术，通讯录里谁是谁？"
	},
	{
		id: "R004",
		name: "银角大王",
		quality: "fine",
		origin: "平顶山",
		relatedProduct: "aitable",
		captureQuote: "紫金红葫芦，装！"
	},
	{
		id: "R005",
		name: "金角大王",
		quality: "fine",
		origin: "平顶山",
		relatedProduct: "aitable",
		captureQuote: "幌金绳，捆！"
	},
	{
		id: "R006",
		name: "红孩儿",
		quality: "fine",
		origin: "火云洞",
		relatedProduct: "ding",
		captureQuote: "三昧真火，DING！"
	},
	{
		id: "R007",
		name: "鼍龙",
		quality: "fine",
		origin: "黑水河",
		relatedProduct: "approval",
		captureQuote: "我舅舅是西海龙王，审批通过！"
	},
	{
		id: "R008",
		name: "蜘蛛精",
		quality: "fine",
		origin: "盘丝洞",
		relatedProduct: "todo",
		captureQuote: "七姐妹的待办，丝丝入扣。"
	},
	{
		id: "R009",
		name: "蝎子精",
		quality: "fine",
		origin: "琵琶洞",
		relatedProduct: "attendance",
		captureQuote: "倒马毒桩，准时打卡。"
	},
	{
		id: "R010",
		name: "六耳猕猴",
		quality: "fine",
		origin: "—",
		relatedProduct: null,
		captureQuote: "真假难辨，你猜我是谁？"
	},
	{
		id: "R011",
		name: "奔波儿灞",
		quality: "fine",
		origin: "乱石山碧波潭",
		relatedProduct: "chat",
		captureQuote: "跑腿送信，我最在行。"
	},
	{
		id: "R012",
		name: "灞波儿奔",
		quality: "fine",
		origin: "乱石山碧波潭",
		relatedProduct: "chat",
		captureQuote: "消息必达，使命必成。"
	},
	{
		id: "R013",
		name: "独角兕大王",
		quality: "fine",
		origin: "金兜山",
		relatedProduct: "calendar",
		captureQuote: "金刚琢套住你的日程。"
	},
	{
		id: "R014",
		name: "如意真仙",
		quality: "fine",
		origin: "解阳山",
		relatedProduct: "report",
		captureQuote: "落胎泉的日报，概不外传。"
	},
	{
		id: "R015",
		name: "虎力大仙",
		quality: "fine",
		origin: "车迟国",
		relatedProduct: "approval",
		captureQuote: "国师审批，一言九鼎。"
	},
	{
		id: "S001",
		name: "黄袍怪",
		quality: "rare",
		origin: "碗子山",
		relatedProduct: "report",
		captureQuote: "百花羞的日报，我替她写了。"
	},
	{
		id: "S002",
		name: "金翅大鹏",
		quality: "rare",
		origin: "狮驼岭",
		relatedProduct: "calendar",
		captureQuote: "翅膀一扇，九万里。日程？不存在的。"
	},
	{
		id: "S003",
		name: "青牛精",
		quality: "rare",
		origin: "金兜山",
		relatedProduct: "aitable",
		captureQuote: "金刚琢，套住你的表格。"
	},
	{
		id: "S004",
		name: "铁扇公主",
		quality: "rare",
		origin: "翠云山",
		relatedProduct: "approval",
		captureQuote: "芭蕉扇一扇，审批全灭。"
	},
	{
		id: "S005",
		name: "牛魔王",
		quality: "rare",
		origin: "积雷山",
		relatedProduct: "workbench",
		captureQuote: "我乃平天大圣，工作台归我管。"
	},
	{
		id: "S006",
		name: "白鹿精",
		quality: "rare",
		origin: "比丘国",
		relatedProduct: "attendance",
		captureQuote: "一千一百一十一个小儿的考勤。"
	},
	{
		id: "S007",
		name: "蜈蚣精",
		quality: "rare",
		origin: "黄花观",
		relatedProduct: "todo",
		captureQuote: "千目待办，一个不漏。"
	},
	{
		id: "S008",
		name: "玉兔精",
		quality: "rare",
		origin: "天竺国",
		relatedProduct: "calendar",
		captureQuote: "广寒宫的排班表，我说了算。"
	},
	{
		id: "S009",
		name: "金鼻白毛老鼠精",
		quality: "rare",
		origin: "无底洞",
		relatedProduct: "contact",
		captureQuote: "无底洞的通讯录，深不见底。"
	},
	{
		id: "S010",
		name: "鹿力大仙",
		quality: "rare",
		origin: "车迟国",
		relatedProduct: "ding",
		captureQuote: "呼风唤雨，DING 声如雷。"
	},
	{
		id: "S011",
		name: "羊力大仙",
		quality: "rare",
		origin: "车迟国",
		relatedProduct: "devdoc",
		captureQuote: "油锅里的文档，捞出来就是。"
	},
	{
		id: "S012",
		name: "荆棘岭十八公",
		quality: "rare",
		origin: "荆棘岭",
		relatedProduct: "chat",
		captureQuote: "松竹梅桂，群聊四友。"
	},
	{
		id: "E001",
		name: "黄眉大王",
		quality: "epic",
		origin: "弥勒佛的童子",
		relatedProduct: "approval",
		captureQuote: "人种袋，把你的审批全装进来。"
	},
	{
		id: "E002",
		name: "大鹏金翅明王",
		quality: "epic",
		origin: "如来舅舅",
		relatedProduct: "workbench",
		captureQuote: "狮驼国的工作台，三界最大。"
	},
	{
		id: "E003",
		name: "九灵元圣",
		quality: "epic",
		origin: "太乙天尊坐骑",
		relatedProduct: "aitable",
		captureQuote: "九个头，九张表，哪个都不能少。"
	},
	{
		id: "E004",
		name: "赛太岁",
		quality: "epic",
		origin: "观音坐骑金毛犼",
		relatedProduct: "attendance",
		captureQuote: "紫金铃一摇，全员到齐。"
	},
	{
		id: "E005",
		name: "青狮精",
		quality: "epic",
		origin: "文殊菩萨坐骑",
		relatedProduct: "chat",
		captureQuote: "狮子吼，群消息已送达。"
	},
	{
		id: "E006",
		name: "白象精",
		quality: "epic",
		origin: "普贤菩萨坐骑",
		relatedProduct: "todo",
		captureQuote: "长鼻一卷，待办清空。"
	},
	{
		id: "E007",
		name: "蠹虫精",
		quality: "epic",
		origin: "比丘国国丈",
		relatedProduct: "report",
		captureQuote: "一千一百一十一份日报，全在这了。"
	},
	{
		id: "E008",
		name: "金鱼精",
		quality: "epic",
		origin: "观音莲花池",
		relatedProduct: "calendar",
		captureQuote: "通天河的日程，年年祭祀。"
	},
	{
		id: "E009",
		name: "蟒蛇精",
		quality: "epic",
		origin: "七绝山",
		relatedProduct: "devdoc",
		captureQuote: "七绝山的文档，毒气弥漫。"
	},
	{
		id: "E010",
		name: "灵感大王",
		quality: "epic",
		origin: "通天河",
		relatedProduct: "ding",
		captureQuote: "金鱼一跃，DING 达四海。"
	},
	{
		id: "L001",
		name: "混世魔王",
		quality: "legendary",
		origin: "花果山第一战",
		relatedProduct: null,
		captureQuote: "水帘洞，从此姓孙。"
	},
	{
		id: "L002",
		name: "牛魔王（魔化）",
		quality: "legendary",
		origin: "大力牛魔王本相",
		relatedProduct: null,
		captureQuote: "平天大圣，不服来战！"
	},
	{
		id: "L003",
		name: "九头虫",
		quality: "legendary",
		origin: "碧波潭万圣龙王驸马",
		relatedProduct: null,
		captureQuote: "九颗头颅，九种权限。"
	},
	{
		id: "L004",
		name: "百眼魔君",
		quality: "legendary",
		origin: "蜈蚣精本相",
		relatedProduct: null,
		captureQuote: "千目金光，洞察一切数据。"
	},
	{
		id: "L005",
		name: "大鹏金翅（本相）",
		quality: "legendary",
		origin: "遮天蔽日",
		relatedProduct: null,
		captureQuote: "三界之大，不过我翅膀之下。"
	},
	{
		id: "L006",
		name: "孙悟空（石猴）",
		quality: "legendary",
		origin: "花果山水帘洞",
		relatedProduct: null,
		captureQuote: "俺老孙来也！"
	},
	{
		id: "L007",
		name: "六耳猕猴（真身）",
		quality: "legendary",
		origin: "混沌之中",
		relatedProduct: null,
		captureQuote: "天地间第二个齐天大圣。"
	},
	{
		id: "L008",
		name: "白骨夫人（真身）",
		quality: "legendary",
		origin: "白虎岭深处",
		relatedProduct: null,
		captureQuote: "三打不死，方显真身。"
	}
];
/**
* 获取所有妖怪
*/
function getAllMonsters() {
	return allMonsters;
}
/**
* 获取指定品质的妖怪列表
*/
function getMonstersByQuality(quality) {
	return allMonsters.filter((m) => m.quality === quality);
}
/**
* 根据 ID 查找妖怪
*/
function getMonsterById(monsterId) {
	return allMonsters.find((m) => m.id === monsterId);
}
/**
* 获取所有妖怪的总数（不含闪光变体）
*/
function getTotalMonsterCount() {
	return allMonsters.length;
}
/**
* 获取本周 UP 妖怪
*
* 按周数轮换，从史诗和传说池中选择
*/
function getWeeklyUpMonster() {
	const upPool = allMonsters.filter((m) => m.quality === "epic" || m.quality === "legendary");
	if (upPool.length === 0) return null;
	return upPool[Math.floor(Date.now() / (10080 * 60 * 1e3)) % upPool.length];
}
/**
* 带权重的随机选择妖怪
*
* @param pool - 候选妖怪池
* @param product - 当前 dws 产品（关联产品权重 ×3）
* @param upMonster - 本周 UP 妖怪（权重 ×5）
* @param randomValue - 随机数 [0, 1)
*/
function weightedRandomSelect(pool, product, upMonster, randomValue) {
	if (pool.length === 0) throw new Error("Monster pool is empty");
	if (pool.length === 1) return pool[0];
	const weights = pool.map((monster) => {
		let weight = 1;
		if (product && monster.relatedProduct === product) weight *= 3;
		if (upMonster && monster.id === upMonster.id) weight *= 5;
		return weight;
	});
	let target = randomValue * weights.reduce((sum, w) => sum + w, 0);
	for (let i = 0; i < pool.length; i++) {
		target -= weights[i];
		if (target <= 0) return pool[i];
	}
	return pool[pool.length - 1];
}
//#endregion
//#region src/game-xiyou/drop-engine.ts
/**
* 概率掉落引擎（核心）
*
* 每次 dws CLI 成功执行后触发一次"降妖"事件。
* 流程：保底判定 → 随机品质 → 等级门槛降级 → 加权选妖 → 闪光判定 → 更新计数器
*/
/**
* 使用 crypto.randomBytes 生成安全随机数
*/
function cryptoRandom$2() {
	return randomBytes(4).readUInt32BE(0) / 4294967295;
}
/**
* 根据随机数和用户等级判定掉落品质
*
* v2: 集成软保底概率加成
*/
function resolveQuality(roll, level, buffs, softPityBonuses) {
	const rateBonus = {};
	for (const buff of buffs) switch (buff.effect) {
		case "epicRateBonus":
			rateBonus.epic = (rateBonus.epic ?? 0) + buff.value;
			break;
		case "rareRateBonus":
			rateBonus.rare = (rateBonus.rare ?? 0) + buff.value;
			break;
		case "legendaryRateBonus":
			rateBonus.legendary = (rateBonus.legendary ?? 0) + buff.value;
			break;
		case "shinyRateBonus":
			rateBonus.shiny = (rateBonus.shiny ?? 0) + buff.value;
			break;
		case "allRateBonus":
			for (const quality of QUALITY_ORDER) if (quality !== "normal" && quality !== "fine") rateBonus[quality] = (rateBonus[quality] ?? 0) + buff.value;
			break;
	}
	for (const [quality, bonus] of Object.entries(softPityBonuses)) {
		const qualityKey = quality;
		rateBonus[qualityKey] = (rateBonus[qualityKey] ?? 0) + (bonus ?? 0);
	}
	let cumulative = 0;
	for (const quality of [
		"shiny",
		"legendary",
		"epic",
		"rare",
		"fine",
		"normal"
	]) {
		const baseRate = DROP_RATES[quality];
		const bonus = rateBonus[quality] ?? 0;
		cumulative += baseRate + bonus;
		if (roll < cumulative) return quality;
	}
	return "normal";
}
/**
* 应用等级门槛降级
*/
function applyLevelGate(quality, level) {
	const gate = QUALITY_LEVEL_GATES[quality];
	if (gate !== void 0 && level < gate) {
		const qualityIndex = QUALITY_ORDER.indexOf(quality);
		for (let i = qualityIndex - 1; i >= 0; i--) {
			const lowerQuality = QUALITY_ORDER[i];
			const lowerGate = QUALITY_LEVEL_GATES[lowerQuality];
			if (lowerGate === void 0 || level >= lowerGate) return lowerQuality;
		}
		return "normal";
	}
	return quality;
}
/**
* 检查玲珑宝塔 buff：普通掉落有概率升级为精良
*/
function checkNormalUpgrade(quality, buffs) {
	if (quality !== "normal") return quality;
	const upgradeChance = buffs.filter((b) => b.effect === "normalUpgrade").reduce((sum, b) => sum + b.value, 0);
	if (upgradeChance > 0 && cryptoRandom$2() < upgradeChance) return "fine";
	return quality;
}
/**
* 将品质提升一级（用于月光宝盒事件）
*/
function boostQuality(quality) {
	const index = QUALITY_ORDER.indexOf(quality);
	if (index < 0 || index >= QUALITY_ORDER.length - 1) return quality;
	return QUALITY_ORDER[index + 1];
}
/**
* 执行一次掉落
*
* v2: 集成软保底概率加成、事件品质提升/上限、禁止掉落检查
*/
function executeDrop(product, profile, collection) {
	const emptyResult = {
		monster: {
			id: "",
			name: "",
			quality: "normal",
			origin: "",
			relatedProduct: null,
			captureQuote: ""
		},
		isShiny: false,
		isNew: false,
		expGained: 0,
		isPityTriggered: false,
		isUpMonster: false,
		escaped: false,
		escapeRate: 0,
		escapeModifiers: []
	};
	if (isDropSuppressed(profile)) return emptyResult;
	const pity = profile.pityCounters;
	let isPityTriggered = false;
	let quality;
	const pityQuality = checkPityTrigger(pity);
	if (pityQuality) {
		quality = pityQuality;
		isPityTriggered = true;
	} else {
		const roll = cryptoRandom$2();
		const softPityBonuses = getSoftPityBonuses(pity);
		quality = resolveQuality(roll, profile.level, profile.buffs, softPityBonuses);
	}
	quality = applyLevelGate(quality, profile.level);
	quality = checkNormalUpgrade(quality, profile.buffs);
	const qualityCap = getQualityCap(profile);
	if (qualityCap) {
		const capIndex = QUALITY_ORDER.indexOf(qualityCap);
		if (QUALITY_ORDER.indexOf(quality) > capIndex) quality = qualityCap;
	}
	const qualityBoostLevel = getQualityBoost(profile);
	if (qualityBoostLevel > 0) {
		for (let i = 0; i < qualityBoostLevel; i++) quality = boostQuality(quality);
		quality = applyLevelGate(quality, profile.level);
	}
	let isShiny = false;
	if (quality === "shiny") {
		isShiny = true;
		const availableQualities = QUALITY_ORDER.filter((q) => {
			if (q === "shiny") return false;
			const gate = QUALITY_LEVEL_GATES[q];
			return gate === void 0 || profile.level >= gate;
		});
		quality = availableQualities[Math.floor(cryptoRandom$2() * availableQualities.length)] || "normal";
	} else if (profile.level >= 9) {
		const shinyBonus = profile.buffs.filter((b) => b.effect === "shinyRateBonus").reduce((sum, b) => sum + b.value, 0);
		if (cryptoRandom$2() < .001 + shinyBonus) isShiny = true;
	}
	const pool = getMonstersByQuality(quality);
	const upMonster = getWeeklyUpMonster();
	let monster;
	if (pool.length === 0) monster = weightedRandomSelect(getMonstersByQuality("normal"), product, null, cryptoRandom$2());
	else monster = weightedRandomSelect(pool, product, upMonster, cryptoRandom$2());
	const isNew = !collection.entries.some((e) => e.monsterId === monster.id && (isShiny ? e.isShiny : !e.isShiny));
	updatePityCounters(pity, quality, isShiny);
	return {
		monster,
		isShiny,
		isNew,
		expGained: 0,
		isPityTriggered,
		isUpMonster: upMonster?.id === monster.id,
		escaped: false,
		escapeRate: 0,
		escapeModifiers: []
	};
}
//#endregion
//#region src/game-xiyou/treasure-system.ts
/**
* 法宝数据（内联，导出供 encounter-system 引用）
*/
const TREASURES_DATA = [
	{
		id: "jintouyun",
		name: "筋斗云",
		source: "菩提祖师赐宝",
		description: "连击加成额外 +0.5",
		effect: "comboBonus",
		value: .5,
		consumable: false
	},
	{
		id: "jingping",
		name: "净瓶",
		source: "观音菩萨赐宝",
		description: "recovery 成功时额外 +5 修行值",
		effect: "expMultiplier",
		value: 1.1,
		consumable: false
	},
	{
		id: "zijinhulu",
		name: "紫金葫芦",
		source: "太上老君赐宝",
		description: "每日额外 1 次掉落机会",
		effect: "extraDrop",
		value: 1,
		consumable: false
	},
	{
		id: "pantao",
		name: "蟠桃",
		source: "太白金星赐宝",
		description: "使用后立即 +50 修行值",
		effect: "instantExp",
		value: 50,
		consumable: true
	},
	{
		id: "qiankunquan",
		name: "乾坤圈",
		source: "哪吒赐宝",
		description: "闪光概率 +0.05%",
		effect: "shinyRateBonus",
		value: 5e-4,
		consumable: false
	},
	{
		id: "sanjiandao",
		name: "三尖两刃刀",
		source: "二郎真君赐宝",
		description: "CLI 错误自动重试 +1 次",
		effect: "cliRetry",
		value: 1,
		consumable: false
	},
	{
		id: "linglongta",
		name: "玲珑宝塔",
		source: "托塔天王赐宝",
		description: "普通掉落 20% 概率升级为精良",
		effect: "normalUpgrade",
		value: .2,
		consumable: false
	},
	{
		id: "renshenguo",
		name: "人参果",
		source: "镇元大仙赐宝",
		description: "使用后立即 +200 修行值",
		effect: "instantExp",
		value: 200,
		consumable: true
	},
	{
		id: "dinghaishenzhen",
		name: "定海神针",
		source: "成就「齐天大圣」解锁",
		description: "所有掉落率 +1%",
		effect: "allRateBonus",
		value: .01,
		consumable: false
	},
	{
		id: "jingguzhou",
		name: "紧箍咒",
		source: "成就「西天取经」解锁",
		description: "保底计数器速度 ×1.5",
		effect: "pitySpeed",
		value: 1.5,
		consumable: false
	},
	{
		id: "bashanshan",
		name: "芭蕉扇",
		source: "收服铁扇公主后概率获得",
		description: "连续签到奖励 ×2",
		effect: "signInMultiplier",
		value: 2,
		consumable: false
	},
	{
		id: "zhaoyaojing",
		name: "照妖镜",
		source: "收服全部精良妖怪后解锁",
		description: "掉落时预览下一次的品质",
		effect: "previewNextQuality",
		value: 1,
		consumable: false
	}
];
const allTreasures = TREASURES_DATA;
/**
* 根据 ID 查找法宝
*/
function getTreasureById(treasureId) {
	return allTreasures.find((t) => t.id === treasureId);
}
/**
* 获取用户拥有的法宝列表（含详情）
*/
function getUserTreasures(profile) {
	return profile.treasures.map((id) => getTreasureById(id)).filter((t) => t !== void 0);
}
/**
* 获取用户可使用的一次性法宝
*/
function getConsumableTreasures(profile) {
	return getUserTreasures(profile).filter((t) => t.consumable && !profile.consumedTreasures.includes(t.id));
}
/**
* 使用一次性法宝
*
* @returns 使用结果描述，或 null（法宝不存在/已使用/不可消耗）
*/
function consumeTreasure(profile, treasureName) {
	const treasure = allTreasures.find((t) => t.name === treasureName);
	if (!treasure) return null;
	if (!profile.treasures.includes(treasure.id)) return null;
	if (!treasure.consumable) return null;
	if (profile.consumedTreasures.includes(treasure.id)) return null;
	profile.consumedTreasures.push(treasure.id);
	let expGained = 0;
	let message = "";
	if (treasure.effect === "instantExp") {
		expGained = treasure.value;
		profile.totalExp += expGained;
		message = `修行值 +${expGained}`;
	}
	return {
		treasure,
		expGained,
		message
	};
}
//#endregion
//#region src/game-xiyou/encounter-system.ts
/**
* 神仙机缘系统
*
* 等级 ≥ 3（修行者）后解锁。
* 每次 dws CLI 成功执行，除了掉落妖怪外，还有独立概率触发"神仙机缘"事件。
*/
/**
* 神仙数据（内联）
*/
const allImmortals = [
	{
		id: "G001",
		name: "菩提祖师",
		guidanceQuote: "悟性不错，但还差一个筋斗云的距离。",
		treasureId: "jintouyun",
		apprenticeBuff: {
			id: "putizu-apprentice",
			source: "apprentice",
			effect: "expMultiplier",
			value: 1.2
		}
	},
	{
		id: "G002",
		name: "观音菩萨",
		guidanceQuote: "救苦救难，先把待办清了。",
		treasureId: "jingping",
		apprenticeBuff: {
			id: "guanyin-apprentice",
			source: "apprentice",
			effect: "pityReduction",
			value: .5
		}
	},
	{
		id: "G003",
		name: "太上老君",
		guidanceQuote: "八卦炉里炼出来的，都是好东西。",
		treasureId: "zijinhulu",
		apprenticeBuff: {
			id: "laojun-apprentice",
			source: "apprentice",
			effect: "epicRateBonus",
			value: .01
		}
	},
	{
		id: "G004",
		name: "太白金星",
		guidanceQuote: "玉帝有旨，你的 KPI 不错。",
		treasureId: "pantao",
		apprenticeBuff: {
			id: "taibai-apprentice",
			source: "apprentice",
			effect: "signInMultiplier",
			value: 1.5
		}
	},
	{
		id: "G005",
		name: "哪吒三太子",
		guidanceQuote: "风火轮转得快，但别忘了刹车。",
		treasureId: "qiankunquan",
		apprenticeBuff: {
			id: "nezha-apprentice",
			source: "apprentice",
			effect: "comboLimitBonus",
			value: 1
		}
	},
	{
		id: "G006",
		name: "二郎真君",
		guidanceQuote: "第三只眼看穿一切 bug。",
		treasureId: "sanjiandao",
		apprenticeBuff: {
			id: "erlang-apprentice",
			source: "apprentice",
			effect: "rareRateBonus",
			value: .02
		}
	},
	{
		id: "G007",
		name: "托塔天王",
		guidanceQuote: "塔在手，妖魔走。",
		treasureId: "linglongta",
		apprenticeBuff: {
			id: "tuota-apprentice",
			source: "apprentice",
			effect: "allRateBonus",
			value: .005
		}
	},
	{
		id: "G008",
		name: "镇元大仙",
		guidanceQuote: "人参果，三千年一开花，三千年一结果。",
		treasureId: "renshenguo",
		apprenticeBuff: {
			id: "zhenyuan-apprentice",
			source: "apprentice",
			effect: "legendaryRateBonus",
			value: .003
		}
	}
];
function cryptoRandom$1() {
	return randomBytes(4).readUInt32BE(0) / 4294967295;
}
/**
* 根据 ID 查找神仙
*/
function getImmortalById(immortalId) {
	return allImmortals.find((i) => i.id === immortalId);
}
/**
* 获取法宝名称
*/
function getTreasureName(treasureId) {
	return TREASURES_DATA.find((t) => t.id === treasureId)?.name ?? treasureId;
}
/**
* 获取法宝描述
*/
function getTreasureDescription(treasureId) {
	return TREASURES_DATA.find((t) => t.id === treasureId)?.description ?? "";
}
/**
* 检查是否触发机缘事件
*
* @returns 机缘事件，或 null（未触发）
*/
function checkEncounter(profile) {
	if (profile.level < 3) return null;
	for (const encounterType of [
		"apprentice",
		"treasure",
		"guidance"
	]) {
		const rate = ENCOUNTER_RATES[encounterType];
		if (cryptoRandom$1() < rate) {
			const immortal = allImmortals[Math.floor(cryptoRandom$1() * allImmortals.length)];
			const encounter = {
				immortalId: immortal.id,
				type: encounterType,
				occurredAt: Date.now()
			};
			if (encounterType === "treasure") encounter.treasureId = immortal.treasureId;
			if (encounterType === "apprentice") encounter.buffId = immortal.apprenticeBuff.id;
			return encounter;
		}
	}
	return null;
}
/**
* 应用机缘效果到用户档案
*/
function applyEncounterEffects(profile, encounter) {
	profile.encounters.push(encounter);
	const immortal = getImmortalById(encounter.immortalId);
	if (!immortal) return;
	if (encounter.type === "treasure" && encounter.treasureId) {
		if (!profile.treasures.includes(encounter.treasureId)) profile.treasures.push(encounter.treasureId);
		const treasure = TREASURES_DATA.find((t) => t.id === encounter.treasureId);
		if (treasure && !treasure.consumable) {
			if (!profile.buffs.find((b) => b.id === treasure.id)) profile.buffs.push({
				id: treasure.id,
				source: "treasure",
				effect: treasure.effect,
				value: treasure.value
			});
		}
	}
	if (encounter.type === "apprentice") {
		const buff = { ...immortal.apprenticeBuff };
		if (!profile.buffs.find((b) => b.id === buff.id)) profile.buffs.push(buff);
	}
}
//#endregion
//#region src/game-xiyou/achievement-engine.ts
/**
* 成就数据（内联）
*/
const allAchievements = [
	{
		id: "A001",
		name: "初出茅庐",
		emoji: "🐒",
		description: "首次成功调用 dws CLI",
		category: "cultivation",
		condition: {
			type: "totalOperations",
			count: 1
		},
		expReward: 10
	},
	{
		id: "A002",
		name: "三天打鱼",
		emoji: "🔥",
		description: "连续 3 天签到",
		category: "cultivation",
		condition: {
			type: "consecutiveSignIn",
			days: 3
		},
		expReward: 15
	},
	{
		id: "A003",
		name: "七七四十九",
		emoji: "📅",
		description: "连续 49 天签到",
		category: "cultivation",
		condition: {
			type: "consecutiveSignIn",
			days: 49
		},
		expReward: 200
	},
	{
		id: "A004",
		name: "十连斩",
		emoji: "⚡",
		description: "单次连击达到 10 次",
		category: "cultivation",
		condition: {
			type: "maxCombo",
			count: 10
		},
		expReward: 50
	},
	{
		id: "A005",
		name: "五行山下",
		emoji: "🏔️",
		description: "累计 500 次成功调用",
		category: "cultivation",
		condition: {
			type: "totalOperations",
			count: 500
		},
		expReward: 100
	},
	{
		id: "A006",
		name: "八十一难",
		emoji: "🌋",
		description: "累计 81 次 recovery 成功",
		category: "cultivation",
		condition: {
			type: "totalRecoveries",
			count: 81
		},
		expReward: 300
	},
	{
		id: "A101",
		name: "妖怪猎人",
		emoji: "📖",
		description: "收服 10 种不同妖怪",
		category: "collection",
		condition: {
			type: "uniqueMonsters",
			count: 10
		},
		expReward: 30
	},
	{
		id: "A102",
		name: "半部西游",
		emoji: "📚",
		description: "收服 24 种不同妖怪",
		category: "collection",
		condition: {
			type: "uniqueMonsters",
			count: 24
		},
		expReward: 100
	},
	{
		id: "A103",
		name: "妖魔全书",
		emoji: "📜",
		description: "收服全部 48 种妖怪",
		category: "collection",
		condition: {
			type: "uniqueMonsters",
			count: 48
		},
		expReward: 500,
		titleReward: "妖魔克星"
	},
	{
		id: "A104",
		name: "闪光猎人",
		emoji: "✨",
		description: "收服 1 只闪光妖怪",
		category: "collection",
		condition: {
			type: "shinyMonsters",
			count: 1
		},
		expReward: 200
	},
	{
		id: "A105",
		name: "闪光大师",
		emoji: "🌈",
		description: "收服 5 只闪光妖怪",
		category: "collection",
		condition: {
			type: "shinyMonsters",
			count: 5
		},
		expReward: 500,
		titleReward: "欧皇"
	},
	{
		id: "A106",
		name: "全闪通关",
		emoji: "👑",
		description: "收服 10 只闪光妖怪",
		category: "collection",
		condition: {
			type: "shinyMonsters",
			count: 10
		},
		expReward: 1e3,
		titleReward: "天选之人"
	},
	{
		id: "A201",
		name: "表格大师",
		emoji: "📊",
		description: "aitable 相关命令成功 50 次",
		category: "product",
		condition: {
			type: "productUsage",
			product: "aitable",
			count: 50
		},
		expReward: 30
	},
	{
		id: "A202",
		name: "时间管理者",
		emoji: "📅",
		description: "calendar 相关命令成功 50 次",
		category: "product",
		condition: {
			type: "productUsage",
			product: "calendar",
			count: 50
		},
		expReward: 30
	},
	{
		id: "A203",
		name: "群聊达人",
		emoji: "💬",
		description: "chat 相关命令成功 50 次",
		category: "product",
		condition: {
			type: "productUsage",
			product: "chat",
			count: 50
		},
		expReward: 30
	},
	{
		id: "A204",
		name: "待办终结者",
		emoji: "✅",
		description: "todo 相关命令成功 50 次",
		category: "product",
		condition: {
			type: "productUsage",
			product: "todo",
			count: 50
		},
		expReward: 30
	},
	{
		id: "A205",
		name: "日报之王",
		emoji: "📝",
		description: "report 连续 30 天提交",
		category: "product",
		condition: {
			type: "consecutiveReport",
			days: 30
		},
		expReward: 100
	},
	{
		id: "A206",
		name: "全能战士",
		emoji: "🎯",
		description: "使用过所有 11 个产品",
		category: "product",
		condition: { type: "allProducts" },
		expReward: 200
	},
	{
		id: "A301",
		name: "夜猫子",
		emoji: "🌙",
		description: "凌晨 2:00-5:00 成功调用",
		category: "hidden",
		condition: { type: "nightOwl" },
		expReward: 20
	},
	{
		id: "A302",
		name: "非酋翻身",
		emoji: "🎰",
		description: "触发天命保底（150 次未出传说）",
		category: "hidden",
		condition: { type: "pityTriggered" },
		expReward: 100,
		titleReward: "大器晚成"
	},
	{
		id: "A303",
		name: "屡败屡战",
		emoji: "💀",
		description: "连续 10 次失败后第 11 次成功",
		category: "hidden",
		condition: {
			type: "consecutiveFailThenSuccess",
			failCount: 10
		},
		expReward: 50
	},
	{
		id: "A304",
		name: "屠龙勇士",
		emoji: "🐉",
		description: "单日收服 3 只稀有及以上妖怪",
		category: "hidden",
		condition: {
			type: "dailyRareOrAbove",
			count: 3
		},
		expReward: 100
	},
	{
		id: "A305",
		name: "生日快乐",
		emoji: "🎂",
		description: "在账号注册日当天使用",
		category: "hidden",
		condition: { type: "birthday" },
		expReward: 50
	},
	{
		id: "A401",
		name: "逃跑大师",
		emoji: "💨",
		description: "累计被妖怪逃跑 50 次",
		category: "hidden",
		condition: {
			type: "totalEscapes",
			count: 50
		},
		expReward: 30
	},
	{
		id: "A402",
		name: "一网打尽",
		emoji: "🪤",
		description: "连续 10 次掉落无妖怪逃跑",
		category: "hidden",
		condition: {
			type: "consecutiveNoEscape",
			count: 10
		},
		expReward: 50
	},
	{
		id: "A403",
		name: "赏金猎人",
		emoji: "📜",
		description: "累计完成 30 张悬赏令",
		category: "hidden",
		condition: {
			type: "totalBountiesCompleted",
			count: 30
		},
		expReward: 100,
		titleReward: "赏金猎人"
	},
	{
		id: "A404",
		name: "金牌猎人",
		emoji: "🥇",
		description: "累计完成 10 张金令",
		category: "hidden",
		condition: {
			type: "goldBountiesCompleted",
			count: 10
		},
		expReward: 150
	},
	{
		id: "A405",
		name: "全勤猎人",
		emoji: "📅",
		description: "连续 7 天每日完成全部 3 张悬赏令",
		category: "hidden",
		condition: {
			type: "consecutiveFullClear",
			days: 7
		},
		expReward: 200
	},
	{
		id: "A406",
		name: "见多识广",
		emoji: "🎪",
		description: "累计触发 10 次随机事件",
		category: "hidden",
		condition: {
			type: "totalEventsTriggered",
			count: 10
		},
		expReward: 30
	},
	{
		id: "A407",
		name: "百战百胜",
		emoji: "⚔️",
		description: "累计完成 10 次挑战事件",
		category: "hidden",
		condition: {
			type: "challengesCompleted",
			count: 10
		},
		expReward: 100,
		titleReward: "战神"
	},
	{
		id: "A408",
		name: "劫后余生",
		emoji: "😈",
		description: "触发「走火入魔」后存活（修行值未归零）",
		category: "hidden",
		condition: { type: "survivedMadness" },
		expReward: 50,
		titleReward: "大难不死"
	},
	{
		id: "A409",
		name: "蟠桃常客",
		emoji: "🍑",
		description: "累计触发 3 次「蟠桃大会」",
		category: "hidden",
		condition: {
			type: "specificEventCount",
			eventId: "EV001",
			count: 3
		},
		expReward: 80
	},
	{
		id: "A410",
		name: "火焰山主",
		emoji: "🔥",
		description: "累计完成 3 次「火焰山」挑战",
		category: "hidden",
		condition: {
			type: "specificEventCount",
			eventId: "EV102",
			count: 3
		},
		expReward: 60
	},
	{
		id: "A411",
		name: "真假悟空",
		emoji: "🐒",
		description: "在「真假美猴王」事件中选对",
		category: "hidden",
		condition: {
			type: "specificChallengeSuccess",
			eventId: "EV104"
		},
		expReward: 100,
		titleReward: "火眼金睛"
	},
	{
		id: "A412",
		name: "否极泰来",
		emoji: "🌈",
		description: "灾厄事件结束后立即触发增益事件",
		category: "hidden",
		condition: { type: "disasterThenBlessing" },
		expReward: 200
	},
	{
		id: "A413",
		name: "化险为夷",
		emoji: "🛡️",
		description: "累计 5 次通过化解方式提前解除灾厄",
		category: "hidden",
		condition: {
			type: "disastersResolved",
			count: 5
		},
		expReward: 80
	}
];
/**
* 获取所有成就
*/
function getAllAchievements() {
	return allAchievements;
}
/**
* 根据 ID 查找成就
*/
function getAchievementById(achievementId) {
	return allAchievements.find((a) => a.id === achievementId);
}
/**
* 检查单个成就条件是否满足
*/
function isConditionMet(condition, profile, collection, todayRecords) {
	switch (condition.type) {
		case "totalOperations": return profile.totalOperations >= condition.count;
		case "consecutiveSignIn": return profile.consecutiveSignInDays >= condition.days;
		case "maxCombo": return profile.maxCombo >= condition.count;
		case "totalRecoveries": return profile.totalRecoveries >= condition.count;
		case "uniqueMonsters": return collection.entries.filter((e) => !e.isShiny).length >= condition.count;
		case "shinyMonsters": return collection.entries.filter((e) => e.isShiny).length >= condition.count;
		case "productUsage": return (profile.productUsage[condition.product] ?? 0) >= condition.count;
		case "allProducts": return Object.keys(PRODUCT_BASE_EXP).every((p) => (profile.productUsage[p] ?? 0) > 0);
		case "dailyOperations": return todayRecords.filter((r) => r.success).length >= condition.count;
		case "nightOwl": {
			const hour = (/* @__PURE__ */ new Date()).getHours();
			return hour >= 2 && hour < 5;
		}
		case "pityTriggered": return false;
		case "consecutiveFailThenSuccess": return profile.consecutiveFailures >= condition.failCount;
		case "dailyRareOrAbove": return todayRecords.filter((r) => {
			if (!r.monsterId) return false;
			return r.monsterId.startsWith("S") || r.monsterId.startsWith("E") || r.monsterId.startsWith("L");
		}).length >= condition.count;
		case "birthday": {
			const createdDate = new Date(profile.createdAt);
			const now = /* @__PURE__ */ new Date();
			return createdDate.getMonth() === now.getMonth() && createdDate.getDate() === now.getDate() && now.getFullYear() > createdDate.getFullYear();
		}
		case "consecutiveReport": return (profile.productUsage["report"] ?? 0) >= condition.days;
		case "totalEscapes": return profile.totalEscapes >= condition.count;
		case "consecutiveNoEscape": return false;
		case "totalBountiesCompleted": return profile.bountyHistory.totalCompleted >= condition.count;
		case "goldBountiesCompleted": return profile.bountyHistory.goldCompleted >= condition.count;
		case "consecutiveFullClear": return profile.bountyHistory.consecutiveFullClear >= condition.days;
		case "totalEventsTriggered": return profile.eventStats.totalTriggered >= condition.count;
		case "challengesCompleted": return profile.eventStats.challengesCompleted >= condition.count;
		case "survivedMadness": return profile.eventHistory.some((e) => e.eventId === "EV206") && profile.totalExp > 0;
		case "specificEventCount": return profile.eventHistory.filter((e) => e.eventId === condition.eventId).length >= condition.count;
		case "specificChallengeSuccess": return profile.eventHistory.some((e) => e.eventId === condition.eventId && e.outcome === "success");
		case "disasterThenBlessing": return false;
		case "disastersResolved": return profile.eventStats.disastersResolved >= condition.count;
		default: return false;
	}
}
/**
* 检查所有未解锁的成就，返回新解锁的成就列表
*/
function checkAchievements(profile, collection, todayRecords) {
	const newlyUnlocked = [];
	for (const achievement of allAchievements) {
		if (profile.unlockedAchievements.includes(achievement.id)) continue;
		if (isConditionMet(achievement.condition, profile, collection, todayRecords)) {
			newlyUnlocked.push(achievement);
			profile.unlockedAchievements.push(achievement.id);
		}
	}
	return newlyUnlocked;
}
/**
* 手动触发特殊成就（如保底触发）
*/
function triggerSpecialAchievement(profile, achievementId) {
	if (profile.unlockedAchievements.includes(achievementId)) return null;
	const achievement = getAchievementById(achievementId);
	if (!achievement) return null;
	profile.unlockedAchievements.push(achievementId);
	return achievement;
}
//#endregion
//#region src/game-xiyou/escape-engine.ts
/**
* 妖怪逃跑引擎 (v2)
*
* 掉落不再等于收服。品质越高的妖怪越难降服。
* 逃跑率受连击、法宝、buff、产品关联等因素修正，最低不低于 5%。
* 保底触发的妖怪 100% 收服，不会逃跑。
*/
function cryptoRandom() {
	return randomBytes(4).readUInt32BE(0) / 4294967295;
}
/**
* 计算逃跑率修正因子列表
*/
function calculateEscapeModifiers(monster, profile, product, isBountyTarget) {
	const modifiers = [];
	if (profile.currentCombo >= 10) modifiers.push({
		source: "combo",
		value: .2,
		description: `连击 ×${profile.currentCombo} 加成`
	});
	else if (profile.currentCombo >= 5) modifiers.push({
		source: "combo",
		value: .1,
		description: `连击 ×${profile.currentCombo} 加成`
	});
	if (profile.buffs.some((b) => b.id === "linglongta")) modifiers.push({
		source: "treasure",
		value: .15,
		description: "玲珑宝塔"
	});
	if (profile.buffs.some((b) => b.id === "dinghaishenzhen")) modifiers.push({
		source: "treasure",
		value: .1,
		description: "定海神针"
	});
	if (profile.buffs.some((b) => b.id === "erlang-apprentice")) modifiers.push({
		source: "buff",
		value: .08,
		description: "二郎真君师徒"
	});
	if (monster.relatedProduct && monster.relatedProduct === product) modifiers.push({
		source: "product",
		value: .05,
		description: "产品关联匹配"
	});
	if (isBountyTarget) modifiers.push({
		source: "bounty",
		value: .1,
		description: "悬赏令加成"
	});
	for (const event of profile.activeEvents.currentEvents) if (event.effect.type === "escape_rate_mod") {
		const eventValue = Math.abs(event.effect.value);
		if (event.effect.value < 0) modifiers.push({
			source: "event",
			value: eventValue,
			description: `${event.name} 减益`
		});
	}
	return modifiers;
}
/**
* 计算最终逃跑率
*/
function calculateFinalEscapeRate(quality, isShiny, modifiers, profile, monsterId) {
	const baseRate = isShiny ? BASE_ESCAPE_RATES.shiny : BASE_ESCAPE_RATES[quality];
	if (baseRate === 0) return 0;
	const totalReduction = modifiers.reduce((sum, m) => sum + m.value, 0);
	let eventIncrease = 0;
	for (const event of profile.activeEvents.currentEvents) if (event.effect.type === "escape_rate_mod" && event.effect.value > 0) eventIncrease += event.effect.value;
	const consecutiveEscapes = profile.escapeHistory[monsterId] ?? 0;
	let consecutiveReduction = 0;
	if (consecutiveEscapes >= 3) consecutiveReduction = (baseRate + eventIncrease - totalReduction) * .5;
	const finalRate = baseRate + eventIncrease - totalReduction - consecutiveReduction;
	return Math.max(MIN_ESCAPE_RATE, Math.min(finalRate, .95));
}
/**
* 判定妖怪是否逃跑，并更新追踪数据
*
* @returns 更新后的 DropResult（设置 escaped / escapeRate / escapeModifiers）
*/
function resolveEscape(dropResult, profile, product, isBountyTarget = false) {
	const { monster, isShiny, isPityTriggered } = dropResult;
	if (isPityTriggered) return {
		...dropResult,
		escaped: false,
		escapeRate: 0,
		escapeModifiers: []
	};
	if (monster.quality === "normal" && !isShiny) return {
		...dropResult,
		escaped: false,
		escapeRate: 0,
		escapeModifiers: []
	};
	const modifiers = calculateEscapeModifiers(monster, profile, product, isBountyTarget);
	const escapeRate = calculateFinalEscapeRate(monster.quality, isShiny, modifiers, profile, monster.id);
	const escaped = cryptoRandom() < escapeRate;
	if (escaped) {
		profile.escapeHistory[monster.id] = (profile.escapeHistory[monster.id] ?? 0) + 1;
		profile.totalEscapes += 1;
	} else profile.escapeHistory[monster.id] = 0;
	return {
		...dropResult,
		escaped,
		escapeRate,
		escapeModifiers: modifiers
	};
}
//#endregion
//#region src/game-xiyou/renderer.ts
/**
* 渲染普通掉落结果（追加到 agent 回复末尾）
*/
function renderDropResult(drop, expResult, collection) {
	if (!drop.monster.id) return "";
	const qualityLabel = drop.isShiny ? "✨ 闪光" : QUALITY_LABELS[drop.monster.quality];
	const totalMonsters = getTotalMonsterCount();
	const collectedCount = collection.entries.length;
	if (drop.escaped) {
		const escapeLines = [
			"",
			"---",
			`💨 ${qualityLabel} **${drop.monster.name}** 挣脱束缚，遁入云中！`,
			`> "${drop.monster.captureQuote}"`,
			`修行值 +2（安慰奖）`
		];
		if (drop.escapeModifiers.length > 0) {
			const modDesc = drop.escapeModifiers.map((m) => `${m.description} -${Math.floor(m.value * 100)}%`).join("、");
			escapeLines.push(`*已生效减益：${modDesc}*`);
		}
		escapeLines.push(`💡 *连击越高，收服成功率越大*`);
		return escapeLines.join("\n");
	}
	if (drop.isShiny) return [
		"",
		"---",
		"🌈🌈🌈 **闪光降临！** 🌈🌈🌈",
		"",
		`✨ **${drop.monster.name} ✨**`,
		`*闪光变体 · 极其稀有*`,
		`> "${drop.monster.captureQuote}"`,
		"",
		`修行值 +${expResult.totalExp} · 图鉴 ${collectedCount}/${totalMonsters}`,
		drop.isPityTriggered ? "🔮 *保底触发*" : "",
		drop.isUpMonster ? "📢 *本周 UP*" : ""
	].filter(Boolean).join("\n");
	if (drop.monster.quality === "epic" || drop.monster.quality === "legendary") return [
		"",
		"---",
		`✦✦✦ **${qualityLabel}降临！** ✦✦✦`,
		"",
		`**${drop.monster.name}**`,
		`*${drop.monster.origin}*`,
		`> "${drop.monster.captureQuote}"`,
		"",
		`修行值 +${expResult.totalExp} · 图鉴 ${collectedCount}/${totalMonsters}`,
		drop.isPityTriggered ? "🔮 *保底触发*" : "",
		drop.isUpMonster ? "📢 *本周 UP*" : ""
	].filter(Boolean).join("\n");
	if (drop.isNew) return [
		"",
		"---",
		`📖 **图鉴新发现！**`,
		"",
		`${qualityLabel} **${drop.monster.name}** · ${drop.monster.origin}`,
		`> "${drop.monster.captureQuote}"`,
		"",
		`修行值 +${expResult.totalExp}${expResult.firstUseMultiplier > 1 ? " (首次 ×5)" : ""} · 图鉴 ${collectedCount}/${totalMonsters}`
	].join("\n");
	return [
		"",
		"---",
		`🗡️ **降妖成功！** 收服了 ${qualityLabel} ${drop.monster.name}`,
		`> "${drop.monster.captureQuote}"`,
		"",
		`修行值 +${expResult.totalExp} · 图鉴 ${collectedCount}/${totalMonsters}`
	].join("\n");
}
function renderLevelUp(levelUp) {
	const lines = [
		"",
		"---",
		`⬆️ **修为精进！** ${levelUp.previousTitle} → ${levelUp.newTitle} (Lv.${levelUp.newLevel})`
	];
	const quote = {
		2: "菩提祖师云：尚可造化。",
		3: "菩提祖师云：悟性不错，可堪造化。",
		4: "天庭来报：准予散仙之位。",
		5: "玉帝有旨：封为天兵。",
		6: "托塔天王令：升任天将。",
		7: "太乙真人赞：有哪吒之勇。",
		8: "玉帝惊叹：堪比二郎神。",
		9: "如来佛祖：齐天大圣，名不虚传。",
		10: "如来佛祖：善哉善哉，封斗战胜佛。"
	}[levelUp.newLevel];
	if (quote) lines.push(`> "${quote}"`);
	if (levelUp.unlockDescription) lines.push("", `🔓 解锁：${levelUp.unlockDescription}`);
	return lines.join("\n");
}
function renderEncounter(encounter) {
	const immortal = getImmortalById(encounter.immortalId);
	if (!immortal) return "";
	const lines = [
		"",
		"---",
		`☁️ **机缘降临！**`,
		"",
		`**${immortal.name}** 驾云而过：`,
		`> "${immortal.guidanceQuote}"`
	];
	if (encounter.type === "treasure" && encounter.treasureId) {
		const treasureName = getTreasureName(encounter.treasureId);
		const treasureDesc = getTreasureDescription(encounter.treasureId);
		lines.push("", `💛 **赐宝**：${treasureName}`, `效果：${treasureDesc}`);
	}
	if (encounter.type === "apprentice") lines.push("", `💜 **收徒**：${immortal.name}收你为徒，获得永久加成！`);
	return lines.join("\n");
}
function renderNewAchievements(achievements) {
	if (achievements.length === 0) return "";
	const lines = ["", "---"];
	for (const achievement of achievements) {
		lines.push(`🏆 **成就解锁！** ${achievement.emoji} ${achievement.name}`, `*${achievement.description}*`, `修行值 +${achievement.expReward}`);
		if (achievement.titleReward) lines.push(`🎖️ 获得称号：「${achievement.titleReward}」`);
	}
	return lines.join("\n");
}
/**
* 渲染修行面板 (/修行)
*/
function renderProfilePanel(profile, collection) {
	const totalMonsters = getTotalMonsterCount();
	const collectedCount = collection.entries.length;
	const shinyCount = collection.entries.filter((e) => e.isShiny).length;
	const progress = getLevelProgress(profile.totalExp);
	const expToNext = getExpToNextLevel(profile.totalExp);
	const nextLevel = getNextLevel(profile.level);
	const upMonster = getWeeklyUpMonster();
	const allAchievementsList = getAllAchievements();
	const filledBlocks = Math.floor(progress / 5);
	const emptyBlocks = 20 - filledBlocks;
	const progressBar = "▓".repeat(filledBlocks) + "░".repeat(emptyBlocks);
	const lines = [
		`### 🐒 西游妖魔榜 · 修行面板`,
		"",
		`**修行者 ID**：${profile.uidHash.slice(0, 8)}`,
		`**称号**：${profile.title} (Lv.${profile.level})`
	];
	if (nextLevel) lines.push(`**修行值**：${profile.totalExp.toLocaleString()} / ${nextLevel.requiredExp.toLocaleString()} (${progress}%)`, "", `${progressBar}`, "", `距离下一级「${nextLevel.title}」还需 ${expToNext?.toLocaleString()} 修行值`);
	else lines.push(`**修行值**：${profile.totalExp.toLocaleString()} (已满级)`, "", `${"▓".repeat(20)}`);
	lines.push("", `#### 📊 统计`, `- **总操作**：${profile.totalOperations} 次`, `- **连击中**：${profile.currentCombo} 次${profile.currentCombo >= 3 ? ` (×${getComboDisplay(profile.currentCombo)})` : ""}`, `- **连续签到**：${profile.consecutiveSignInDays} 天`, `- **最高连击**：${profile.maxCombo} 次`);
	const qualityCounts = getQualityProgress(collection);
	lines.push("", `#### 📖 图鉴 ${collectedCount}/${totalMonsters} (${Math.floor(collectedCount / totalMonsters * 100)}%)`, "", `| 品质 | 进度 |`, `|------|------|`);
	for (const [label, collected, total] of qualityCounts) {
		const status = collected >= total ? " ✅" : "";
		lines.push(`| ${label} | ${collected}/${total}${status} |`);
	}
	if (shinyCount > 0) lines.push(`| ✨ 闪光 | ${shinyCount} |`);
	const pity = profile.pityCounters;
	lines.push("", `#### 🔮 保底状态`, `- **小保底**：${pity.sinceLastRare}/30 · **大保底**：${pity.sinceLastEpic}/80 · **天命**：${pity.sinceLastLegendary}/150`);
	if (upMonster) lines.push("", `📢 **本周 UP**：${QUALITY_LABELS[upMonster.quality]} ${upMonster.name} (权重 ×5)`);
	lines.push("", `🏆 **成就**：${profile.unlockedAchievements.length}/${allAchievementsList.length}`, `🎒 **法宝**：${profile.treasures.length} 件`);
	return lines.join("\n");
}
/**
* 渲染图鉴面板 (/图鉴)
*/
function renderCollectionPanel(collection) {
	const allMonstersList = getAllMonsters();
	const totalMonsters = getTotalMonsterCount();
	const lines = [`### 📖 妖怪图鉴 · ${collection.entries.length}/${totalMonsters}`, ""];
	const qualityGroups = [
		{
			quality: "normal",
			label: "⬜ 普通",
			monsters: allMonstersList.filter((m) => m.quality === "normal")
		},
		{
			quality: "fine",
			label: "🟢 精良",
			monsters: allMonstersList.filter((m) => m.quality === "fine")
		},
		{
			quality: "rare",
			label: "🔵 稀有",
			monsters: allMonstersList.filter((m) => m.quality === "rare")
		},
		{
			quality: "epic",
			label: "🟣 史诗",
			monsters: allMonstersList.filter((m) => m.quality === "epic")
		},
		{
			quality: "legendary",
			label: "🟡 传说",
			monsters: allMonstersList.filter((m) => m.quality === "legendary")
		}
	];
	for (const group of qualityGroups) {
		const collected = group.monsters.filter((m) => collection.entries.some((e) => e.monsterId === m.id && !e.isShiny));
		const uncollectedCount = group.monsters.length - collected.length;
		lines.push(`#### ${group.label} ${collected.length}/${group.monsters.length}${collected.length >= group.monsters.length ? " ✅" : ""}`);
		if (collected.length > 0) lines.push(collected.map((m) => m.name).join(" · "));
		if (uncollectedCount > 0) lines.push(`${"❓".repeat(Math.min(uncollectedCount, 5))} *还有 ${uncollectedCount} 只未发现*`);
		lines.push("");
	}
	const shinyEntries = collection.entries.filter((e) => e.isShiny);
	lines.push(`#### ✨ 闪光 ${shinyEntries.length}`);
	if (shinyEntries.length > 0) {
		const shinyNames = shinyEntries.map((e) => {
			const monster = getMonsterById(e.monsterId);
			return monster ? `${monster.name} ✨` : e.monsterId;
		});
		lines.push(shinyNames.join(" · "));
	} else lines.push("*等级 ≥ 9 后解锁闪光掉落*");
	return lines.join("\n");
}
/**
* 渲染成就面板 (/成就)
*/
function renderAchievementPanel(profile) {
	const allAchievementsList = getAllAchievements();
	const lines = [`### 🏆 成就列表 · ${profile.unlockedAchievements.length}/${allAchievementsList.length}`, ""];
	for (const category of [
		{
			key: "cultivation",
			label: "修行成就"
		},
		{
			key: "collection",
			label: "收集成就"
		},
		{
			key: "product",
			label: "产品成就"
		},
		{
			key: "hidden",
			label: "隐藏成就"
		}
	]) {
		const categoryAchievements = allAchievementsList.filter((a) => a.category === category.key);
		lines.push(`#### ${category.label}`);
		for (const achievement of categoryAchievements) {
			const unlocked = profile.unlockedAchievements.includes(achievement.id);
			const status = unlocked ? "✅" : "⬜";
			const desc = category.key === "hidden" && !unlocked ? "???" : achievement.description;
			lines.push(`- ${status} ${achievement.emoji} **${achievement.name}** — ${desc} (+${achievement.expReward})`);
		}
		lines.push("");
	}
	return lines.join("\n");
}
/**
* 渲染法宝面板 (/法宝)
*/
function renderTreasurePanel(profile) {
	const treasures = getUserTreasures(profile);
	const consumable = getConsumableTreasures(profile);
	const lines = [`### 🎒 法宝背包 · ${treasures.length} 件`, ""];
	if (treasures.length === 0) {
		lines.push("*背包空空如也，等待神仙赐宝...*");
		return lines.join("\n");
	}
	for (const treasure of treasures) {
		const status = profile.consumedTreasures.includes(treasure.id) ? "（已使用）" : treasure.consumable ? "（可使用）" : "（永久生效）";
		lines.push(`- **${treasure.name}** ${status}`, `  ${treasure.description}`, `  *来源：${treasure.source}*`, "");
	}
	if (consumable.length > 0) lines.push("", `💡 发送 \`/使用 法宝名\` 来使用一次性法宝`);
	return lines.join("\n");
}
/**
* 渲染保底面板 (/保底)
*/
function renderPityPanel(profile) {
	const pity = profile.pityCounters;
	const softPityHints = [];
	if (pity.sinceLastRare >= 20) softPityHints.push(`稀有软保底已激活 +${(pity.sinceLastRare - 20) * 3}%`);
	if (pity.sinceLastEpic >= 60) softPityHints.push(`史诗软保底已激活 +${(pity.sinceLastEpic - 60) * 2}%`);
	if (pity.sinceLastLegendary >= 120) softPityHints.push(`传说软保底已激活 +${(pity.sinceLastLegendary - 120) * 1}%`);
	const lines = [
		`### 🔮 保底计数器`,
		"",
		`| 保底类型 | 当前计数 | 触发阈值 | 进度 |`,
		`|---------|---------|---------|------|`,
		`| 小保底（稀有） | ${pity.sinceLastRare} | 30 | ${Math.floor(pity.sinceLastRare / 30 * 100)}% |`,
		`| 大保底（史诗） | ${pity.sinceLastEpic} | 80 | ${Math.floor(pity.sinceLastEpic / 80 * 100)}% |`,
		`| 天命保底（传说） | ${pity.sinceLastLegendary} | 150 | ${Math.floor(pity.sinceLastLegendary / 150 * 100)}% |`,
		`| 闪光保底 | ${pity.totalDropsWithoutShiny} | 800 | ${Math.floor(pity.totalDropsWithoutShiny / 800 * 100)}% |`
	];
	if (softPityHints.length > 0) lines.push("", `🌟 ${softPityHints.join(" · ")}`);
	lines.push("", `*保底计数器在对应品质或更高品质掉落后重置*`);
	return lines.join("\n");
}
/**
* 渲染机缘面板 (/机缘)
*/
function renderEncounterPanel(profile) {
	const lines = [`### ☁️ 神仙机缘录`, ""];
	if (profile.level < 3) {
		lines.push("*等级 ≥ 3（修行者）后解锁机缘系统*");
		return lines.join("\n");
	}
	if (profile.encounters.length === 0) {
		lines.push("*尚未遇到任何神仙，继续修行吧...*");
		return lines.join("\n");
	}
	for (const encounter of profile.encounters) {
		const immortal = getImmortalById(encounter.immortalId);
		if (!immortal) continue;
		const typeLabel = encounter.type === "guidance" ? "🤍 点化" : encounter.type === "treasure" ? "💛 赐宝" : "💜 收徒";
		const date = new Date(encounter.occurredAt).toLocaleDateString("zh-CN");
		lines.push(`- ${typeLabel} **${immortal.name}** — ${date}`);
		if (encounter.type === "treasure" && encounter.treasureId) lines.push(`  赐宝：${getTreasureName(encounter.treasureId)}`);
	}
	return lines.join("\n");
}
/**
* 渲染妖魔榜 (/妖魔榜)
*/
function renderLeaderboard(profile, collection) {
	const upMonster = getWeeklyUpMonster();
	const totalMonsters = getTotalMonsterCount();
	const lines = [`### 🐒 西游妖魔榜`, ""];
	if (upMonster) lines.push(`#### 📢 本周 UP`, `${QUALITY_LABELS[upMonster.quality]} **${upMonster.name}** · ${upMonster.origin}`, `> "${upMonster.captureQuote}"`, `*在对应品质池中掉落权重 ×5*`, "");
	lines.push(`#### 📊 掉落统计`, `- **总掉落**：${profile.totalOperations} 次`, `- **图鉴完成度**：${collection.entries.length}/${totalMonsters}`, `- **闪光收服**：${collection.entries.filter((e) => e.isShiny).length} 只`, "", `#### 🔮 保底状态`, `- 小保底：${profile.pityCounters.sinceLastRare}/30`, `- 大保底：${profile.pityCounters.sinceLastEpic}/80`, `- 天命：${profile.pityCounters.sinceLastLegendary}/150`);
	return lines.join("\n");
}
/**
* 渲染法宝使用结果
*/
function renderTreasureUse(treasureName, expGained, currentExp, nextLevelExp) {
	return [
		"---",
		`${{
			"蟠桃": "🍑",
			"人参果": "🍐"
		}[treasureName] ?? "✨"} **使用了${treasureName}！**`,
		`修行值 +${expGained}${nextLevelExp ? ` · 当前 ${currentExp}/${nextLevelExp}` : ""}`,
		`> "仙物入腹，周身舒泰。"`
	].join("\n");
}
/**
* 渲染群聊炫耀 (/炫耀)
*/
function renderShowOff(profile, collection) {
	const shinyCount = collection.entries.filter((e) => e.isShiny).length;
	const rarest = findRarestMonster(collection);
	const lines = [
		`### 🐒 ${profile.title} (Lv.${profile.level}) 的西游妖魔榜`,
		"",
		`图鉴：${collection.entries.length}/${getTotalMonsterCount()} · 闪光：${shinyCount}`
	];
	if (rarest) lines.push(`最稀有：${QUALITY_LABELS[rarest.quality]} ${rarest.name}`);
	lines.push("", `> "此人修为不浅，诸位小心。"`);
	return lines.join("\n");
}
function getComboDisplay(combo) {
	if (combo >= 10) return "3.0";
	if (combo >= 5) return "2.0";
	if (combo >= 3) return "1.5";
	return "1.0";
}
function getQualityProgress(collection) {
	const allMonstersList = getAllMonsters();
	return [
		{
			label: "⬜ 普通",
			quality: "normal"
		},
		{
			label: "🟢 精良",
			quality: "fine"
		},
		{
			label: "🔵 稀有",
			quality: "rare"
		},
		{
			label: "🟣 史诗",
			quality: "epic"
		},
		{
			label: "🟡 传说",
			quality: "legendary"
		}
	].map(({ label, quality }) => {
		const total = allMonstersList.filter((m) => m.quality === quality).length;
		return [
			label,
			allMonstersList.filter((m) => m.quality === quality && collection.entries.some((e) => e.monsterId === m.id && !e.isShiny)).length,
			total
		];
	});
}
function findRarestMonster(collection) {
	for (const quality of [
		"legendary",
		"epic",
		"rare",
		"fine",
		"normal"
	]) {
		const entry = collection.entries.find((e) => {
			return getMonsterById(e.monsterId)?.quality === quality;
		});
		if (entry) return getMonsterById(entry.monsterId) ?? null;
	}
	return null;
}
const BOUNTY_TIER_LABELS = {
	bronze: "🥉 铜令",
	silver: "🥈 银令",
	gold: "🥇 金令"
};
/**
* 渲染悬赏令面板 (/悬赏)
*/
function renderBountyPanel(profile) {
	const bountyState = profile.dailyBounty;
	if (!bountyState || bountyState.bounties.length === 0) return [
		`### 📜 今日悬赏令`,
		"",
		"*今日悬赏令尚未生成，执行一次 dws 命令即可刷新。*"
	].join("\n");
	const lines = [`### 📜 今日悬赏令`, ""];
	for (const bounty of bountyState.bounties) {
		const tierLabel = BOUNTY_TIER_LABELS[bounty.tier] ?? bounty.tier;
		const status = bounty.completed ? "✅" : "⬜";
		const progressPercent = Math.min(100, Math.floor(bounty.current / bounty.target * 100));
		const filledBlocks = Math.floor(progressPercent / 10);
		const emptyBlocks = 10 - filledBlocks;
		const progressBar = "█".repeat(filledBlocks) + "░".repeat(emptyBlocks);
		lines.push(`${status} **${tierLabel}**：${bounty.description}`, `   奖励：+${bounty.reward.exp} 修行值`, `   进度：${bounty.current}/${bounty.target} ${progressBar} ${progressPercent}%`, "");
	}
	const now = /* @__PURE__ */ new Date();
	const tomorrow = new Date(now);
	tomorrow.setHours(24, 0, 0, 0);
	const remainingMs = tomorrow.getTime() - now.getTime();
	const remainingHours = Math.floor(remainingMs / (3600 * 1e3));
	const remainingMinutes = Math.floor(remainingMs % (3600 * 1e3) / (60 * 1e3));
	lines.push(`⏰ 刷新倒计时：${remainingHours} 小时 ${remainingMinutes} 分`);
	const history = profile.bountyHistory;
	lines.push("", `#### 📊 悬赏历史`, `累计完成：${history.totalCompleted} 张 (🥉${history.bronzeCompleted} 🥈${history.silverCompleted} 🥇${history.goldCompleted})`, `连续全清：${history.consecutiveFullClear} 天`);
	return lines.join("\n");
}
/**
* 渲染悬赏令完成通知
*/
function renderBountyComplete(bounty) {
	return [
		"",
		"---",
		`📜 **${BOUNTY_TIER_LABELS[bounty.tier] ?? bounty.tier}完成！** 「${bounty.description}」`,
		`奖励已发放：修行值 +${bounty.reward.exp}`
	].join("\n");
}
const EVENT_CATEGORY_EMOJI = {
	blessing: "🌟",
	challenge: "⚔️",
	disaster: "😈"
};
/**
* 渲染随机事件触发通知
*/
function renderEventTrigger(event) {
	const lines = [
		"",
		"---",
		`${EVENT_CATEGORY_EMOJI[event.category] ?? "🎲"} **随机事件：${event.name}！**`,
		"",
		`*${event.flavorText}*`,
		""
	];
	if (event.category === "blessing") {
		lines.push(`🌟 **效果**：${event.description}`);
		if (event.duration.type !== "instant") lines.push(`剩余次数：${event.duration.remaining}/${event.duration.total}`);
	}
	if (event.category === "challenge") {
		const challenge = event;
		lines.push(`⚔️ **挑战**：${event.description}`, `🏆 成功：+${challenge.successReward.exp} 修行值${challenge.successReward.pityBonus ? ` + 保底 +${challenge.successReward.pityBonus}` : ""}`, `💀 失败：修行值 -${challenge.failurePenalty.expLoss}${challenge.failurePenalty.comboReset ? " + 连击归零" : ""}`, `⏰ 时限：${challenge.operationLimit} 次操作内完成`, "", `当前进度：${challenge.challengeCondition.current}/${challenge.challengeCondition.target}`);
	}
	if (event.category === "disaster") {
		lines.push(`😈 **效果**：${event.description}`);
		if (event.resolution) lines.push(`💡 **化解**：${event.resolution.description}`);
		if (event.duration.type !== "instant") lines.push(`剩余次数：${event.duration.remaining}/${event.duration.total}`);
	}
	return lines.join("\n");
}
/**
* 渲染挑战事件结果
*/
function renderChallengeResult(event, success) {
	if (success) return [
		"",
		"---",
		`🏆 **${event.name} · 挑战成功！**`,
		"",
		`奖励已发放：修行值 +${event.successReward.exp}`,
		event.successReward.pityBonus ? `保底计数器 +${event.successReward.pityBonus}` : ""
	].filter(Boolean).join("\n");
	return [
		"",
		"---",
		`💀 **${event.name} · 挑战失败**`,
		"",
		`惩罚：修行值 -${event.failurePenalty.expLoss}`,
		event.failurePenalty.comboReset ? "连击已归零" : ""
	].filter(Boolean).join("\n");
}
/**
* 渲染灾厄事件化解通知
*/
function renderDisasterResolved(event) {
	return [
		"",
		"---",
		`🛡️ **${event.name} · 已化解！**`,
		`*灾厄消散，天地清明。*`
	].join("\n");
}
/**
* 渲染事件面板 (/事件)
*/
function renderEventPanel(profile) {
	const activeState = profile.activeEvents;
	const lines = [`### 🎲 随机事件`, ""];
	if (activeState.currentEvents.length === 0 && !activeState.activeChallenge) lines.push("*当前没有活跃的随机事件。*");
	else {
		if (activeState.currentEvents.length > 0) {
			lines.push(`#### 当前生效`);
			for (const event of activeState.currentEvents) {
				const emoji = EVENT_CATEGORY_EMOJI[event.category] ?? "🎲";
				const remaining = event.duration.type !== "instant" ? ` (剩余 ${event.duration.remaining}/${event.duration.total})` : "";
				lines.push(`- ${emoji} **${event.name}**：${event.description}${remaining}`);
				if (event.resolution) lines.push(`  💡 化解：${event.resolution.description}`);
			}
			lines.push("");
		}
		if (activeState.activeChallenge) {
			const challenge = activeState.activeChallenge;
			lines.push(`#### ⚔️ 进行中的挑战`, `**${challenge.name}**：${challenge.description}`, `进度：${challenge.challengeCondition.current}/${challenge.challengeCondition.target}`, `操作次数：${challenge.progress.operationsUsed}/${challenge.progress.operationLimit}`, "");
		}
	}
	const stats = profile.eventStats;
	lines.push(`#### 📊 事件统计`, `- **累计触发**：${stats.totalTriggered} 次`, `- **挑战完成**：${stats.challengesCompleted} 次`, `- **挑战失败**：${stats.challengesFailed} 次`, `- **灾厄化解**：${stats.disastersResolved} 次`);
	return lines.join("\n");
}
//#endregion
//#region src/game-xiyou/commands.ts
/** 养成系统支持的命令列表 */
const GAMIFICATION_COMMANDS = [
	"/修行",
	"/图鉴",
	"/成就",
	"/法宝",
	"/使用",
	"/妖魔榜",
	"/机缘",
	"/保底",
	"/炫耀",
	"/悬赏",
	"/事件",
	"/西游"
];
/**
* 检查消息是否是养成系统命令
*/
function isGamificationCommand(text) {
	const trimmed = text.trim();
	return GAMIFICATION_COMMANDS.some((cmd) => trimmed.startsWith(cmd));
}
/**
* 处理养成系统命令，返回 Markdown 响应
*
* @returns Markdown 字符串，或 null（不是养成系统命令）
*/
function handleGamificationCommand(text, profile, collection, saveCallback) {
	const trimmed = text.trim();
	if (trimmed === "/修行") return renderProfilePanel(profile, collection);
	if (trimmed === "/图鉴") return renderCollectionPanel(collection);
	if (trimmed.startsWith("/图鉴 ")) return renderMonsterDetail(trimmed.slice(4).trim(), collection);
	if (trimmed === "/成就") return renderAchievementPanel(profile);
	if (trimmed === "/法宝") return renderTreasurePanel(profile);
	if (trimmed.startsWith("/使用 ")) return handleUseTreasure(profile, trimmed.slice(4).trim(), saveCallback);
	if (trimmed === "/妖魔榜") return renderLeaderboard(profile, collection);
	if (trimmed === "/机缘") return renderEncounterPanel(profile);
	if (trimmed === "/保底") return renderPityPanel(profile);
	if (trimmed === "/炫耀") return renderShowOff(profile, collection);
	if (trimmed === "/悬赏" || trimmed === "/悬赏 历史") return renderBountyPanel(profile);
	if (trimmed === "/事件" || trimmed === "/事件 历史") return renderEventPanel(profile);
	if (trimmed === "/西游" || trimmed === "/西游 --h" || trimmed === "/西游 -h" || trimmed === "/西游 help") return [
		`### 🐒 西游妖魔榜 · 命令一览`,
		``,
		`当前状态：${profile.settings.enabled ? "✅ 已开启" : "❌ 已关闭"}`,
		``,
		`| 命令 | 功能 |`,
		`|------|------|`,
		`| \`/修行\` | 查看个人修行面板（等级、修行值、连击、签到等） |`,
		`| \`/图鉴\` | 查看妖怪图鉴收集进度 |`,
		`| \`/图鉴 妖怪名\` | 查看指定妖怪详情 |`,
		`| \`/成就\` | 查看成就列表及解锁状态 |`,
		`| \`/法宝\` | 查看法宝背包 |`,
		`| \`/使用 法宝名\` | 使用一次性法宝（如蟠桃、人参果） |`,
		`| \`/妖魔榜\` | 查看本周 UP 妖怪、掉落统计、保底状态 |`,
		`| \`/机缘\` | 查看神仙机缘录 |`,
		`| \`/保底\` | 查看保底计数器详情（含软保底状态） |`,
		`| \`/炫耀\` | 生成炫耀卡片 |`,
		`| \`/悬赏\` | 查看今日悬赏令及历史统计 |`,
		`| \`/事件\` | 查看当前活跃事件及事件统计 |`,
		`| \`/西游 开启\` | 开启养成系统 |`,
		`| \`/西游 关闭\` | 关闭养成系统 |`,
		``,
		`> 关闭后，dws 命令执行不再触发降妖掉落，但已有数据会保留。`
	].join("\n");
	if (trimmed === "/西游 开启" || trimmed === "/西游 开") {
		profile.settings.enabled = true;
		saveCallback();
		return [
			`### 🐒 西游妖魔榜 · 已开启`,
			``,
			`✅ 养成系统已开启！每次使用钉钉产品能力都会触发降妖掉落。`,
			``,
			`发送 \`/修行\` 查看你的修行面板。`
		].join("\n");
	}
	if (trimmed === "/西游 关闭" || trimmed === "/西游 关") {
		profile.settings.enabled = false;
		saveCallback();
		return [
			`### 🐒 西游妖魔榜 · 已关闭`,
			``,
			`❌ 养成系统已关闭。dws 命令执行不再触发降妖掉落。`,
			``,
			`你的修行数据已保留，随时可以发送 \`/西游 开启\` 重新开启。`
		].join("\n");
	}
	return null;
}
/**
* 渲染妖怪详情
*/
function renderMonsterDetail(monsterName, collection) {
	const monster = getAllMonsters().find((m) => m.name === monsterName);
	if (!monster) return `未找到名为「${monsterName}」的妖怪。`;
	const entry = collection.entries.find((e) => e.monsterId === monster.id && !e.isShiny);
	const shinyEntry = collection.entries.find((e) => e.monsterId === monster.id && e.isShiny);
	const lines = [
		`### ${QUALITY_LABELS[monster.quality]} ${monster.name}`,
		"",
		`- **出处**：${monster.origin}`,
		`- **关联产品**：${monster.relatedProduct ?? "任意"}`,
		`- **收服台词**："${monster.captureQuote}"`,
		""
	];
	if (entry) lines.push(`✅ **已收服**`, `- 首次收服：${new Date(entry.firstCapturedAt).toLocaleDateString("zh-CN")}`, `- 收服次数：${entry.captureCount}`);
	else lines.push(`❌ **未收服**`);
	if (shinyEntry) lines.push("", `✨ **闪光变体已收服**`);
	return lines.join("\n");
}
/**
* 处理使用法宝命令
*/
function handleUseTreasure(profile, treasureName, saveCallback) {
	const result = consumeTreasure(profile, treasureName);
	if (!result) return `无法使用「${treasureName}」。可能原因：未拥有、已使用、或不是一次性法宝。\n\n发送 \`/法宝\` 查看背包。`;
	const nextLevelExp = getNextLevel(profile.level)?.requiredExp ?? null;
	saveCallback();
	return renderTreasureUse(treasureName, result.expGained, profile.totalExp, nextLevelExp);
}
//#endregion
//#region src/game-xiyou/index.ts
/**
* 西游妖魔榜养成系统 · 入口
*
* GamificationEngine 是养成系统的门面类，统一协调所有子系统。
* 对外暴露两个核心方法：
* - onDwsCommandResult(): 每次 dws CLI 命令执行后调用（成功或失败）
* - handleCommand(): 处理聊天命令（/修行 /图鉴 等）
*/
let engineInstance = null;
var GamificationEngine = class GamificationEngine {
	profile;
	collection;
	history;
	uidHash;
	constructor(senderId) {
		this.uidHash = resolveUid(senderId);
		this.profile = loadProfile(this.uidHash);
		this.collection = loadCollection(this.uidHash);
		this.history = loadHistory(this.uidHash);
	}
	/**
	* 获取或创建引擎实例
	*/
	static getInstance(senderId) {
		const uidHash = resolveUid(senderId);
		if (!engineInstance || engineInstance.uidHash !== uidHash) engineInstance = new GamificationEngine(senderId);
		return engineInstance;
	}
	/**
	* 强制重新加载数据（用于多用户场景）
	*/
	static getInstanceForUser(senderId) {
		return new GamificationEngine(senderId);
	}
	/**
	* 检查养成系统是否启用
	*/
	isEnabled() {
		return this.profile.settings.enabled;
	}
	/**
	* 检查消息是否是养成系统命令
	*/
	isCommand(text) {
		return isGamificationCommand(text);
	}
	/**
	* 处理聊天命令，返回 Markdown 响应
	*/
	handleCommand(text) {
		return handleGamificationCommand(text, this.profile, this.collection, () => this.save());
	}
	/**
	* dws CLI 命令执行后调用（核心方法）
	*
	* v2: 集成逃跑机制、悬赏令、随机事件系统
	*
	* @param product - dws 产品名（如 "aitable"、"calendar"）
	* @param success - 命令是否成功
	* @param commandStr - 原始命令字符串（用于生成 hash）
	* @param isRecovery - 是否为 recovery 成功
	* @returns Markdown 字符串（追加到 agent 回复末尾），或空字符串
	*/
	onDwsCommandResult(product, success, commandStr = "", isRecovery = false) {
		if (!this.isEnabled()) return "";
		const commandHash = createHash("sha256").update(commandStr).digest("hex").slice(0, 16);
		checkBountyDayReset(this.profile);
		generateDailyBounties(this.profile);
		if (!success) {
			this.profile.currentCombo = 0;
			this.profile.consecutiveFailures += 1;
			tickActiveEvents(this.profile, false, product, false);
			this.save();
			return "";
		}
		this.profile.totalOperations += 1;
		this.profile.currentCombo += 1;
		if (this.profile.currentCombo > this.profile.maxCombo) this.profile.maxCombo = this.profile.currentCombo;
		this.profile.productUsage[product] = (this.profile.productUsage[product] ?? 0) + 1;
		if (isRecovery) this.profile.totalRecoveries += 1;
		updateSignInStatus(this.profile);
		const expResult = calculateExp(product, this.profile);
		const eventExpMultiplier = getActiveExpMultiplier(this.profile);
		expResult.totalExp = Math.floor(expResult.totalExp * eventExpMultiplier);
		const levelUp = checkLevelUp(this.profile, expResult.totalExp);
		this.profile.totalExp += expResult.totalExp;
		applyLevelUp(this.profile);
		let dropResult = executeDrop(product, this.profile, this.collection);
		dropResult.expGained = expResult.totalExp;
		if (dropResult.monster.id) dropResult = resolveEscape(dropResult, this.profile, product);
		if (dropResult.monster.id) tickDropEvents(this.profile);
		if (dropResult.monster.id && !dropResult.escaped) this.updateCollection(dropResult.monster.id, dropResult.isShiny, commandHash);
		if (dropResult.escaped) this.profile.totalExp += 2;
		const encounter = checkEncounter(this.profile);
		if (encounter) {
			applyEncounterEffects(this.profile, encounter);
			if (resolveDisasterEvent(this.profile, "trigger_encounter")) {}
		}
		const triggeredEvent = checkRandomEvent(this.profile);
		let extraDropResult = null;
		if (triggeredEvent) {
			if (triggeredEvent.effect.type === "extra_drop") {
				extraDropResult = executeDrop(product, this.profile, this.collection);
				if (extraDropResult.monster.id && !extraDropResult.escaped) this.updateCollection(extraDropResult.monster.id, extraDropResult.isShiny, commandHash);
			}
			if (triggeredEvent.id === "EV202") {
				const fineEntries = this.collection.entries.filter((e) => {
					return getMonsterById(e.monsterId)?.quality === "fine" && !e.isShiny;
				});
				if (fineEntries.length > 0) {
					const removedEntry = fineEntries[Math.floor(Math.random() * fineEntries.length)];
					this.collection.entries = this.collection.entries.filter((e) => e !== removedEntry);
					this.profile.escapeHistory[removedEntry.monsterId] = 1;
				}
			}
		}
		const capturedMonster = dropResult.monster.id !== "" && !dropResult.escaped;
		const eventResults = tickActiveEvents(this.profile, true, product, capturedMonster);
		if (eventResults.some((r) => r.event.category === "disaster" && (r.outcome === "expired" || r.outcome === "resolved")) && triggeredEvent?.category === "blessing") triggerSpecialAchievement(this.profile, "A412");
		const today = (/* @__PURE__ */ new Date()).toISOString().slice(0, 10);
		const todayRecords = this.history.records.filter((r) => {
			return new Date(r.timestamp).toISOString().slice(0, 10) === today;
		});
		const todayProducts = /* @__PURE__ */ new Set();
		const todayQualities = /* @__PURE__ */ new Set();
		for (const record of todayRecords) {
			if (record.success) todayProducts.add(record.product);
			if (record.monsterId && !record.escaped) {
				const monster = getMonsterById(record.monsterId);
				if (monster) todayQualities.add(monster.quality);
			}
		}
		todayProducts.add(product);
		if (capturedMonster) todayQualities.add(dropResult.monster.quality);
		const bountyContext = {
			commandSuccess: true,
			product,
			dropResult: capturedMonster ? dropResult : void 0,
			encounterTriggered: encounter !== null,
			encounterType: encounter?.type,
			currentCombo: this.profile.currentCombo,
			todayProducts,
			todayQualities
		};
		const completedBounties = updateBountyProgress(this.profile, bountyContext);
		if (completedBounties.length > 0) resolveDisasterEvent(this.profile, "complete_bounty");
		const newAchievements = checkAchievements(this.profile, this.collection, todayRecords);
		if (dropResult.isPityTriggered) {
			const pityAchievement = triggerSpecialAchievement(this.profile, "A302");
			if (pityAchievement) newAchievements.push(pityAchievement);
		}
		if (this.profile.consecutiveFailures >= 10) {
			const failAchievement = triggerSpecialAchievement(this.profile, "A303");
			if (failAchievement) newAchievements.push(failAchievement);
		}
		if (triggeredEvent?.id === "EV206" && this.profile.totalExp > 0) {
			const madnessAchievement = triggerSpecialAchievement(this.profile, "A408");
			if (madnessAchievement) newAchievements.push(madnessAchievement);
		}
		for (const achievement of newAchievements) this.profile.totalExp += achievement.expReward;
		applyLevelUp(this.profile);
		this.profile.consecutiveFailures = 0;
		const historyRecord = {
			timestamp: Date.now(),
			product,
			commandHash,
			success: true,
			expGained: expResult.totalExp,
			monsterId: dropResult.monster.id || void 0,
			isShiny: dropResult.isShiny || void 0,
			escaped: dropResult.escaped || void 0,
			encounterId: encounter?.immortalId,
			achievementIds: newAchievements.length > 0 ? newAchievements.map((a) => a.id) : void 0,
			eventId: triggeredEvent?.id,
			completedBountyIds: completedBounties.length > 0 ? completedBounties.map((b) => b.id) : void 0
		};
		this.history.records.push(historyRecord);
		this.save();
		return this.renderOutput(dropResult, expResult, levelUp, encounter, newAchievements, completedBounties, triggeredEvent ?? null, eventResults);
	}
	/**
	* 更新图鉴
	*/
	updateCollection(monsterId, isShiny, commandHash) {
		const existingEntry = this.collection.entries.find((e) => e.monsterId === monsterId && e.isShiny === isShiny);
		if (existingEntry) existingEntry.captureCount += 1;
		else {
			const newEntry = {
				monsterId,
				firstCapturedAt: Date.now(),
				captureCount: 1,
				isShiny
			};
			this.collection.entries.push(newEntry);
		}
	}
	/**
	* 渲染完整输出（追加到 agent 回复末尾的 Markdown）
	*
	* v2: 新增悬赏令完成、随机事件、挑战结果的渲染
	*/
	renderOutput(dropResult, expResult, levelUp, encounter, newAchievements, completedBounties, triggeredEvent, eventResults) {
		const parts = [];
		if (dropResult.monster.id && !(this.profile.settings.muteNormalDrops && dropResult.monster.quality === "normal" && !dropResult.isNew && !dropResult.isShiny && !dropResult.escaped)) parts.push(renderDropResult(dropResult, expResult, this.collection));
		if (levelUp) parts.push(renderLevelUp(levelUp));
		if (encounter) parts.push(renderEncounter(encounter));
		if (triggeredEvent) parts.push(renderEventTrigger(triggeredEvent));
		for (const result of eventResults) {
			if (result.event.category === "challenge") {
				if (result.outcome === "success" || result.outcome === "failure") parts.push(renderChallengeResult(result.event, result.outcome === "success"));
			}
			if (result.event.category === "disaster" && result.outcome === "resolved") parts.push(renderDisasterResolved(result.event));
		}
		for (const bounty of completedBounties) parts.push(renderBountyComplete(bounty));
		if (newAchievements.length > 0) parts.push(renderNewAchievements(newAchievements));
		return parts.join("\n");
	}
	/**
	* 持久化所有数据
	*/
	save() {
		saveProfile(this.profile);
		saveCollection(this.collection);
		saveHistory(this.history);
	}
};
//#endregion
export { GamificationEngine, isGamificationCommand };
