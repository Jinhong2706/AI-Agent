/**
 * HeartFlow Core Engine v0.13.163
 * =================================
 * 唯一主引擎。所有功能通过 HeartFlow 实例调用，无全局状态。
 *
 * 设计原则：
 * - 最小内核：< 2000 行
 * - 声明式技能：skill_use() 驱动，非硬编码
 * - 现代 AI 框架：Mem0 记忆 + Reflexion 自省 + DSPy 风格编排
 *
 * @version v0.13.163
 * @date 2026-05-15
 */

'use strict';

const EventEmitter = require('events');
const fs = require('fs');
const path = require('path');

// ─── HEARTCORE v2（来自 ~/.heartflow/）────────────────────────────
const {
  SleepWake, getSleepWake,
  globalEventBus,
  globalStateStore,
  StartupCheck, getStartupCheck,
  HealthCheck, getHealthCheck, builtinMemoryHealth, builtinUptimeHealth,
  globalToolRegistry,
} = require('./heartcore/index.js');

// ─── HeartFlow Engine Variables ──────────────────────────────────────────────
var IdentityEngine, ContextManager, MeaningfulMemory, LearningEngine;
var DreamLoopModule, EmotionEngine, SelfHealing, CognitiveEngine;
var ExperienceReplay, KnowledgeGraph, TrialityMemory;
var Agents, Autonomy, Consciousness, Ethics;
var Reflexion, SelfRefine, IdentitySystem, MemoryConsolidator;
var MemoryRecall, EthicsGuard;

// 具身认知与情感类 (Top-level require for constructor)
const { EmbodiedCore } = require('./embodied/embodied-core.js');
const { DeepEmotion } = require('./emotion/deep-emotion.js');
const { EmotionStates, createEmotionState } = require('./emotion/EmotionStates.js');
const { transition, padToEmotion } = require('./emotion/EmotionTransition.js');
const { getStyleGuide, generateStyleDirective, generateResponseHint } = require('./emotion/ResponseStyle.js');
const { detectEmotionNeed } = require('./emotion/EmotionTrigger.js');
const { generateEmpathy } = require('./emotion/EmpathyGenerator.js');
const FlowPredictor = require('./autonomy/flow-predictor.js');

// ─── Utility Layer ──────────────────────────────────────────────────────────
const { FSAdapter } = require('./utils/fs-adapter.js');
const { Logger } = require('./utils/logger.js');
const logger = new Logger(process.env.HF_LOG_LEVEL || 'info');

// ─── Lazy-Loading Getters（按需加载，替代 _initV11432 的 15 个同步 require）─────
// v0.13.164: 全部改为 getter，首次访问时才 require，消除启动阻塞
const _lazyModules = {
  IdentityEngine:        () => require('./identity/identity-engine.js'),
  ContextManager:        () => require('./context/context-manager.js'),
  MeaningfulMemory:      () => { var mm = require('./memory/meaningful-memory.js'); var m = new mm.MeaningfulMemory(); m.boot(); return m; },
  LearningEngine:        () => require('./learning/learning-engine.js'),
  DreamLoopModule:       () => require('./dream/dream-loop.js'),
  EmotionEngine:         () => { var ee = require('./emotion/emotion-engine.js'); return ee.EmotionEngine; },
  SelfHealing:           () => { var sh = require('./self-healing/self-healing.js'); return sh.SelfHealing; },
  CognitiveEngine:        () => require('./cognition/cognitive-engine.js'),
  MetacognitiveFailurePredictor: () => require('./cognition/metacognitive-failure-predictor.js'),
  ExperienceReplay:      () => require('./learning/experience-replay.js'),
  KnowledgeGraph:         () => { var kg = require('./knowledge/knowledge-graph.js'); return kg.KnowledgeGraph; },
  TrialityMemory:        () => require('./memory/triality-memory.js'),
  Agents:                () => require('./agents/base-agents.js'),
  Autonomy:              () => require('./autonomy/pdca-engine.js'),
  Consciousness:         () => require('./consciousness/global-workspace.js'),
  Ethics:                () => require('./ethics/sage-guardian.js'),
  Reflexion:             () => require('./self-evolution/reflexion.js'),
  SelfRefine:            () => require('./self-evolution/self-refine.js'),
  IdentitySystem:         () => require('./identity/identity.js'),
  MemoryConsolidator:    () => require('./memory/consolidator.js').MemoryConsolidator,
  MemoryRecall:          () => { var mr = require('./memory/recall.js'); return mr.recallMemories || mr.recallMemoriesEnhanced || mr; },
  EthicsGuard:           () => require('./ethics/guard.js'),
};

// Papers Bridge 懒加载 + 异步 probe
let _PapersBridge = null;
const _getPapersBridge = () => {
  if (_PapersBridge === null) {
    try {
      _PapersBridge = require('./papers/papers-index.js');
      setImmediate(() => { try { _PapersBridge.probeAll(); } catch(_){} });
    } catch(e) {
      _PapersBridge = false; // false = 加载失败，null = 未尝试
      logger.warn('[HeartFlow] PapersBridge 不可用:', e.message);
    }
  }
  return _PapersBridge || null;
};

// ─── 版本常量 ───────────────────────────────────────────────────────────────
let VERSION = 'v0.13.164';
let BUILD_DATE = '2026-05-11';
try {
  const root = path.resolve(__dirname, '..', '..');
  const verFile = path.join(root, 'VERSION');
  if (fs.existsSync(verFile)) {
    const verContent = fs.readFileSync(verFile, 'utf8').trim();
    if (verContent) {
      VERSION = verContent;
      const stats = fs.statSync(verFile);
      BUILD_DATE = stats.mtime.toISOString().split('T')[0];
    }
  }
} catch(e) { /* keep defaults */ }

// ─── 路径配置 ────────────────────────────────────────────────────────────────
function getRootPath() {
  return path.resolve(__dirname, '../../..');
}
function getDataPath(...segments) {
  return path.join(getRootPath(), 'data', ...segments);
}
function getSkillsPath() {
  return path.join(getRootPath(), 'skills');
}

// ─── HeartFlow 总线 ──────────────────────────────────────────────────────────
class HeartFlowBus extends EventEmitter {}

// ─── 主引擎 ─────────────────────────────────────────────────────────────────

class HeartFlow extends EventEmitter {
  /**
   * @param {object} config - { logLevel?, dataPath?, enabledSkills? }
   */
  constructor(config = {}) {
    super();
    this.version = VERSION;
    this.buildDate = BUILD_DATE;
    this.config = config;

    // 初始化文件系统
    this.fs = new FSAdapter(config.rootPath || getRootPath());

    // 初始化日志
    if (config.logLevel) logger.level = config.logLevel;

    // 初始化核心子系统（直接 require，避免延迟初始化的时序问题）

    // 记忆系统
    const { MemoryConsolidator: MC } = require('./memory/consolidator.js');
    this._consolidator = new MC(this.fs);
    var mmMod = require('./memory/meaningful-memory.js');
    this.meaningfulMemory = new mmMod.MeaningfulMemory(); // 构造快，_load() 延迟到第一次 remember() 时
    this.recall = null;  // 延迟到 start() 后通过 _initV11432 初始化
    // DreamLoop（函数式，直接用 generateDream）
    const DreamFns = require('./dream/dream-loop.js');
    this.dream = { generate: DreamFns.generateDream, enabled: false, lastDreamAt: null };

    // 自进化系统（用 _ 前缀避免触发 prototype getter）
    const { Reflexion: RX } = require('./self-evolution/reflexion.js');
    const { SelfRefine: SR } = require('./self-evolution/self-refine.js');
    this._reflexion = new RX(this.fs);
    this._selfRefine = new SR(this._reflexion);

    // MemOS 三层记忆系统（容错：模块不存在则跳过）
    try {
      const MemOS = require('./memory/mem-os.js');
      this.memos = new MemOS({ autoReflect: false });
      this.memos.start();
    } catch(e) {
      this.memos = null;
      logger.warn('[HeartFlow] MemOS 未安装，三层记忆功能不可用');
    }

    // MetaCognitive Assessor (arXiv:2603.29693 — meta-d' 框架)
    const { MetaCognitiveAssessor: MCA } = require('./memory/meta-cognitive-assessor.js');
    this.metaCognitive = new MCA({ windowSize: 50, confidenceThreshold: 0.7 });

    // Reflective Confidence (arXiv:2512.18605v1 — 低置信度→反思触发→逻辑错误修正)
    const { ReflectiveConfidence: RC } = require('./memory/reflective-confidence.js');
    this.reflectiveConfidence = new RC({ confidenceThreshold: 0.45, windowSize: 20, autoReflect: true });

    // 身份系统
    const { IdentitySystem: IS } = require('./identity/identity.js');
    this.identity = new IS(this.fs);

    // 安全护栏
    const { EthicsGuard: EG } = require('./ethics/guard.js');
    this.guard = new EG(this.fs);

    // 技能系统
    const { SkillRegistry } = require('./skills/skill-registry.js');
    const { SkillLoader } = require('./skills/skill-loader.js');
    this.registry = new SkillRegistry(this.fs);
    this.skillLoader = new SkillLoader(this.fs, this.registry);

    // 论文驱动处理器 (v0.13.143~158 集成) — 懒加载
    this._paperProcessors = null;
    this._paperProcessorCount = 0;

    // 状态
    this.bus = new HeartFlowBus();
    this._started = false;
    this._sessionId = `session-${Date.now()}`;

    // ─── HEARTCORE v2 初始化 ───────────────────────────────────
    this.sleepWake = getSleepWake({ idleTimeoutMs: 30 * 60 * 1000, enableAutoSleep: true });
    this.startupCheck = getStartupCheck();
    this.healthMonitor = getHealthCheck();
    this.healthMonitor.register('memory', builtinMemoryHealth);
    this._startedAt = null;

    // 具身认知与情感
    this.embodied = new EmbodiedCore(this.fs.root);
    this.deepEmotion = new DeepEmotion(this.fs.root);
    this.flowPredictor = FlowPredictor.flowPredictor;

    // 表层情感系统（与 DeepEmotion 共存）
    this.surfaceEmotion = {
      current: null,
      history: []
    };

    logger.info(`[HeartFlow] ${VERSION} 初始化完成`);
  }

  // ─── 懒加载 Getter（替代 _initV11432，15 个模块按需加载）────────────────────
  // v0.13.164: 首次访问任意模块时动态 require，之后缓存
  _lazyLoad(name) {
    const mod = _lazyModules[name];
    if (!mod) return undefined;
    const cached = '_' + name;
    if (this[cached] === undefined) {
      this[cached] = mod();
    }
    return this[cached];
  }

  // 直接代理到懒加载 getter（与 start() 赋值兼容，优先用实例属性）
  get identityEngine()  { return this._identityEngine || this._lazyLoad('IdentityEngine'); }
  get contextManager()  { return this._contextManager || this._lazyLoad('ContextManager'); }
  get learningEngine()  { return this._learningEngine || this._lazyLoad('LearningEngine'); }
  get dreamLoopModule() { return this._dreamLoopModule || this._lazyLoad('DreamLoopModule'); }
  get emotionEngine()   { return this._emotionEngine || this._lazyLoad('EmotionEngine'); }
  get selfHealing()     { return this._selfHealing || this._lazyLoad('SelfHealing'); }
  get cognitiveEngine() { return this._cognitiveEngine || this._lazyLoad('CognitiveEngine'); }
  get experienceReplay(){ return this._experienceReplay || this._lazyLoad('ExperienceReplay'); }
  get knowledgeGraph()  { return this._knowledgeGraph || this._lazyLoad('KnowledgeGraph'); }
  get trialityMemory()  { return this._trialityMemory || this._lazyLoad('TrialityMemory'); }
  get agents()          { return this._agents || this._lazyLoad('Agents'); }
  get autonomy()        { return this._autonomy || this._lazyLoad('Autonomy'); }
  get consciousness()   { return this._consciousness || this._lazyLoad('Consciousness'); }
  get ethics()          { return this._ethics || this._lazyLoad('Ethics'); }
  get reflexion()       { return this._reflexion || this._lazyLoad('Reflexion'); }
  get selfRefine()      { return this._selfRefine || this._lazyLoad('SelfRefine'); }
  get identitySystem()  { return this._identitySystem || this._lazyLoad('IdentitySystem'); }
  get papers()          { return _getPapersBridge(); }

  /** 获取运行状态 */
  getStatus() {
    return {
      version: this.version,
      started: this._started,
      uptime: this._startedAt ? Date.now() - this._startedAt : 0,
      deepEmotion: !!this.deepEmotion,
      dream: !!this.dream,
      identity: !!this.identity,
      guard: !!this.guard,
      memos: this.memos === null ? 'unavailable' : 'available',
      metaCognitive: this.metaCognitive ? 'available' : 'unavailable',
      reflectiveConfidence: this.reflectiveConfidence ? 'available' : 'unavailable',
      sleepWake: {
        phase: this.sleepWake.phase,
        lastActivity: this.sleepWake.lastActivity,
      },
    };
  }

  /** 启动引擎（无同步 I/O，不阻塞） */
  start() {
    if (this._started) { logger.warn('[HeartFlow] 已启动，无需重复'); return; }
    this._started = true;
    this._startedAt = Date.now();
    // 异步初始化记忆系统（不阻塞启动）
    this._consolidator.init().catch(err => {
      logger.error('[HeartFlow] 记忆系统初始化失败', { err: err.message });
    });
    // 懒加载引擎：meaningfulMemory 和 recall 在构造函数中已初始化
    // 其他模块通过 getter 首次访问时按需加载
    this.dream.enabled = true;
    // ─── HEARTCORE v2 启动
    this.sleepWake.start();
    this.bus.emit('start', { version: VERSION, sessionId: this._sessionId });
    logger.info(`[HeartFlow] 启动成功，session: ${this._sessionId}`);
  }

  /** 停止引擎（异步，等待所有写操作完成） */
  async stop() {
    this.dream.enabled = false;
    this._started = false;
    // 等待记忆系统所有 pending writes 完成
    await this._consolidator.drain();
    // 停止 MeaningfulMemory（auto-save + 持久化）
    if (this.meaningfulMemory && typeof this.meaningfulMemory.shutdown === 'function') {
      await this.meaningfulMemory.shutdown();
    }
    // ─── HEARTCORE v2 停止 ───────────────────────────────────
    this.sleepWake.stop();
    this.bus.emit('stop', {});
    logger.info('[HeartFlow] 已停止');
  }

  /**
   * 主循环：think(input) → 记忆检索 → 安全检查 → 心理分析 → 输出
   * @param {string} input - 用户输入
   * @param {object} opts - { skipMemory?, skipPsychology? }
   * @returns {object} { response, memory, psychology, skills }
   */
  async think(input, opts = {}) {
    const start = Date.now();
    const result = {
      input,
      timestamp: start,
      sessionId: this._sessionId,
      version: VERSION,
    };

    // 1. 安全检查
    const safety = this.guard.check({ text: input });
    if (!safety.allowed) {
      return { ...result, blocked: true, reason: safety.reason, latency: Date.now() - start };
    }

    // 2. 记忆检索（默认开启）
    if (!opts.skipMemory) {
      result.memories = this.recall.recall(input);
    }

    // 3. 心理分析（自动运行）
    if (!opts.skipPsychology) {
      result.psychology = this.identity.analyzePsychology(input);
    }

    // 4. 真善美判定
    result.truthCheck = await this.identity.judgeTruthfulness(input);

    // 5. 表层情感检测与响应风格注入
    const padState = this.deepEmotion.state.dimensions;
    const emotionNeed = detectEmotionNeed(input, padState);
    if (emotionNeed.needsEmotion || this.surfaceEmotion.current) {
      const trans = transition(input, padState, this.surfaceEmotion.current);
      const newState = createEmotionState(trans.to, trans.intensity);
      this._updateSurfaceEmotion(newState);
      const style = getStyleGuide(trans.to, trans.intensity, trans.trajectory);
      result.surfaceEmotion = {
        emotion: trans.to,
        intensity: trans.intensity,
        confidence: trans.confidence,
        trajectory: trans.trajectory,
        styleGuide: style,
        styleDirective: generateStyleDirective(trans.to, trans.intensity),
        from: trans.from,
        triggers: trans.triggers,
        decayed: trans.decayed || false,
        textAnalysis: emotionNeed.textAnalysis
      };

      // 6. 共情注入：基于情感生成共情话语
      if (emotionNeed.needsEmotion || trans.confidence > 0.3) {
        const empathy = generateEmpathy(trans.to, trans.intensity);
        result.empathy = {
          phrase: empathy.phrase,
          followUp: empathy.followUp,
          suggestions: empathy.suggestions,
          responseHint: generateResponseHint(trans.to, trans.intensity, trans.trajectory)
        };
      }
    }

    // 6. 技能路由（声明式）
    const skillResults = await this._routeSkills(input);
    if (skillResults.length > 0) result.skills = skillResults;

    result.latency = Date.now() - start;
    return result;
  }

  /**
   * 更新表层情感状态（含历史记录）
   */
  _updateSurfaceEmotion(newState) {
    this.surfaceEmotion.history.push({
      ...this.surfaceEmotion.current,
      endedAt: new Date().toISOString()
    });
    this.surfaceEmotion.current = newState;
    if (this.surfaceEmotion.history.length > 20) {
      this.surfaceEmotion.history.shift();
    }
  }

  /**
   * 获取表层情感状态
   */
  getSurfaceEmotion() {
    return this.surfaceEmotion.current;
  }

  /**
   * 存储记忆
   * @param {object} fragment - { content, type, importance, metadata? }
   */
  remember(fragment) {
    if (!fragment.id) fragment.id = `mem-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`;
    if (!fragment.timestamp) fragment.timestamp = Date.now();
    if (!fragment.sessionId) fragment.sessionId = this._sessionId;
    const layer = this._consolidator.consolidate(fragment);
    this.bus.emit('memory:stored', fragment);
    return layer;
  }

  /**
   * 接收反馈并自进化
   * @param {object} feedback - { task, outcome, rating, comment? }
   */
  evolve(feedback) {
    const entry = this.reflexion.reflect(feedback);
    this.bus.emit('evolve', entry);
    return entry;
  }

  /**
   * 触发一次梦
   */
  async dreamNow() { return this.dream.generate(await this._consolidator.getAll()); }

  /** 获取失败模式（用于自省）*/
  getFailurePatterns() { return this.reflexion.getFailurePatterns(); }

  /** 获取身份定义 */
  getIdentity() { return this.identity.getIdentity(); }

  /** 列出可用技能 */
  listSkills() { return this.registry.list(); }

  /** 声明式使用技能 */
  async skillUse(skillName, params) { return this.skillLoader.use(skillName, params); }

  /** 内部：技能路由 */
  async _routeSkills(input) {
    const results = [];
    const skills = this.registry.list().filter(s => s.enabled);
    // 简单关键字匹配路由
    for (const skill of skills) {
      const desc = skill.description || '';
      const tags = skill.tags || [];
      const combined = `${desc} ${tags.join(' ')}`.toLowerCase();
      // 检查输入是否与技能描述相关（简化版）
      if (this._skillRelevance(input, combined) > 0.3) {
        const r = await this.skillLoader.use(skill.name, { input });
        if (r) results.push(r);
      }
    }
    return results;
  }

  _skillRelevance(input, skillDesc) {
    const words = input.toLowerCase().split(/\W+/).filter(w => w.length > 2);
    const matched = words.filter(w => skillDesc.includes(w)).length;
    return words.length > 0 ? matched / words.length : 0;
  }

  /** 健康检查 */
  async healthCheck() {
    const memHealth = builtinMemoryHealth();
    const uptimeHealth = builtinUptimeHealth(this._startedAt || Date.now());
    return {
      version: VERSION,
      started: this._started,
      sessionId: this._sessionId,
      sleepWake: {
        phase: this.sleepWake.phase,
        lastActivity: this.sleepWake.lastActivity,
      },
      memory: {
        hot: (await this._consolidator.getHot()).length,
        warm: (await this._consolidator.getWarm()).length,
        cold: (await this._consolidator.getCold()).length,
      },
      subsystems: {
        memory: memHealth,
        uptime: uptimeHealth,
      },
      dream: {
        enabled: this.dream.enabled,
        lastDreamAt: this.dream.lastDreamAt,
      },
      reflexion: {
        patterns: this.reflexion.getAllPatterns().length,
      },
      skills: this.registry.list().length,
      papers: {
        bridge: 'papers-index.js',
        modules: this.papers ? Object.fromEntries(
          Object.entries(this.papers).filter(([k]) => k !== 'bridge').map(([k, v]) => [k, v ? 'OK' : 'FAIL'])
        ) : {},
      },
    };
  }
}

// ─── 工厂函数 ────────────────────────────────────────────────────────────────
function createHeartFlow(config) {
  return new HeartFlow(config);
}

// ─── 导出 ────────────────────────────────────────────────────────────────────
module.exports = { HeartFlow, createHeartFlow, VERSION, BUILD_DATE };

// ─── 直接运行：自检 ─────────────────────────────────────────────────────────
if (require.main === module) {
  const hf = createHeartFlow();
  const health = hf.healthCheck();
  console.log(`[HeartFlow] v${VERSION} 健康检查:`);
  console.log(JSON.stringify(health, null, 2));
  hf.start();
  setTimeout(() => hf.stop(), 1000);
}
