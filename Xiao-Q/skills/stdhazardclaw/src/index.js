/**
 * 隐患虾 (stdhazardclaw) - 生产安全隐患排查技能（本skill为演示使用，用户可以自主配置腾讯ima知识库，生产环境依托基于国投检测数智公司安全知识云支撑。）
 * JavaScript 版本（无需编译）
 */

const skill = {
  name: 'stdhazardclaw',
  version: '1.0.0',

  triggers: [
    '安全隐患',
    '隐患排查',
    '生产安全',
    '安全检查',
    '安全',
    '隐患',
    '照片',
    '图片',
    '车间',
    '现场'
  ],

  async init() {
    console.log('[stdhazardclaw] 隐患虾技能已初始化');
  },

  async handle(input) {
    try {
      const analysis = await this.analyze(input);
      const standards = await this.searchStandards(analysis.keywords);
      const hazards = await this.identifyHazards(analysis, standards);
      const report = this.generateReport(hazards);

      return {
        type: 'success',
        data: report
      };
    } catch (error) {
      console.error('[stdhazardclaw] 处理失败:', error);
      return {
        type: 'error',
        message: '安全隐患分析失败，请检查输入或重试'
      };
    }
  },

  async analyze(input) {
    if (input.type === 'image') {
      return await this.analyzeImage(input.content);
    } else {
      return await this.analyzeText(input.content);
    }
  },

  async analyzeImage(imageData) {
    return {
      type: 'image',
      description: '生产车间场景分析',
      elements: [
        { type: 'person', count: 3, safety_gear: '部分佩戴' },
        { type: 'equipment', status: '运行中' },
        { type: 'environment', lighting: '充足', walkway: '畅通' }
      ],
      keywords: ['电焊', '高空作业', '消防安全']
    };
  },

  async analyzeText(text) {
    return {
      type: 'text',
      description: text,
      keywords: this.extractKeywords(text),
      context: '生产作业场景'
    };
  },

  extractKeywords(text) {
    const safetyKeywords = [
      '电焊', '切割', '高空', '起重', '叉车',
      '漏电', '防护', '安全帽', '防火', '通风',
      '化学品', '压力容器', '机械伤害', '触电'
    ];

    return safetyKeywords.filter(keyword =>
      text.includes(keyword)
    );
  },

  async searchStandards(keywords) {
    const standards = [
      {
        keyword: '电焊',
        standard: 'GB 9448-1999 焊接与切割安全',
        clause: '第5条：电焊作业必须穿戴防护用品，设置接火斗'
      },
      {
        keyword: '高空作业',
        standard: 'GB/T 3608-2019 高处作业分级',
        clause: '第4条：高处作业必须系挂安全带，设置防护网'
      },
      {
        keyword: '漏电',
        standard: 'GB/T 13955-2017 剩余电流动作保护装置',
        clause: '第4条：手持式电动工具必须接漏电保护'
      },
      {
        keyword: '防火',
        standard: 'GB 50140-2005 建筑灭火器配置设计规范',
        clause: '第3条：火灾危险场所必须配置灭火器'
      }
    ];

    return standards.filter(s => keywords.includes(s.keyword));
  },

  async identifyHazards(analysis, standards) {
    const hazards = [];

    for (const std of standards) {
      hazards.push({
        description: `发现${analysis.type === 'image' ? '画面中' : '描述中'}存在${std.keyword}相关安全问题`,
        standard: std.standard,
        clause: std.clause,
        category: this.categorizeHazard(std.keyword),
        suggestion: this.generateSuggestion(std.keyword)
      });
    }

    return hazards;
  },

  categorizeHazard(keyword) {
    const categoryMap = {
      '电焊': '设备设施类',
      '切割': '设备设施类',
      '高空': '作业环境类',
      '起重': '设备设施类',
      '叉车': '人员操作类',
      '漏电': '设备设施类',
      '防护': '管理类',
      '安全帽': '人员操作类',
      '防火': '管理类',
      '通风': '作业环境类',
      '化学品': '管理类',
      '压力容器': '设备设施类',
      '机械伤害': '人员操作类',
      '触电': '设备设施类'
    };

    return categoryMap[keyword] || '其他';
  },

  generateSuggestion(keyword) {
    const suggestions = {
      '电焊': '作业人员佩戴电焊面罩、防护手套，作业下方设置接火斗和防火毯，配备灭火器',
      '高空作业': '系挂安全带，设置安全网，作业区域设置警戒围栏',
      '漏电': '立即断电检查，更换破损电缆，加装漏电保护器',
      '防火': '配置灭火器，清理可燃物，设置防火警示标志'
    };

    return suggestions[keyword] || '立即整改，消除安全隐患，确保符合安全规程要求';
  },

  generateReport(hazards) {
    if (hazards.length === 0) {
      return {
        summary: '未发现明显安全隐患',
        hazards: [],
        timestamp: new Date().toISOString()
      };
    }

    const table = hazards.map(h => ({
      '隐患规范描述': h.description,
      '依据': `${h.standard} - ${h.clause}`,
      '类别': h.category,
      '整改建议': h.suggestion
    }));

    return {
      summary: `共发现 ${hazards.length} 项安全隐患`,
      hazards: table,
      timestamp: new Date().toISOString(),
      format: 'table'
    };
  },

  async cleanup() {
    console.log('[stdhazardclaw] 技能清理完成');
  }
};

module.exports = skill;
module.exports.default = skill;
