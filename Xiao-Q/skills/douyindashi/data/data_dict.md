# 抖音运营大师 - 数据字典

## 数据目录结构
```
data/
├── industry_benchmarks.json    # 行业基准数据
├── title_formulas.json         # 标题公式库
├── hot_topics.json             # 热门话题
└── account_data.json            # 账号数据模板
```

---

## 一、行业基准数据 (industry_benchmarks.json)

```json
{
  "美食": {
    "avg_views": 8500,
    "completion_rate": {
      "30s": {"excellent": 50, "good": 40, "average": 30},
      "60s": {"excellent": 45, "good": 35, "average": 25}
    },
    "interaction_rate": {"excellent": 10, "good": 5, "average": 3},
    "fan_rate": {"excellent": 3, "good": 1.5, "average": 0.5},
    "optimal_time": ["11:00-12:00", "17:00-18:00", "20:00-21:00"]
  },
  "美妆": {
    "avg_views": 12000,
    "completion_rate": {
      "30s": {"excellent": 55, "good": 45, "average": 35},
      "60s": {"excellent": 50, "good": 40, "average": 30}
    },
    "interaction_rate": {"excellent": 12, "good": 6, "average": 4},
    "fan_rate": {"excellent": 4, "good": 2, "average": 1},
    "optimal_time": ["20:00-22:00", "12:00-13:00"]
  },
  "知识": {
    "avg_views": 6000,
    "completion_rate": {
      "60s": {"excellent": 40, "good": 30, "average": 22},
      "180s": {"excellent": 35, "good": 25, "average": 18}
    },
    "interaction_rate": {"excellent": 8, "good": 4, "average": 2.5},
    "fan_rate": {"excellent": 2.5, "good": 1.2, "average": 0.5},
    "optimal_time": ["12:00-13:00", "20:00-21:00"]
  },
  "职场": {
    "avg_views": 7500,
    "completion_rate": {
      "60s": {"excellent": 42, "good": 32, "average": 24},
      "180s": {"excellent": 38, "good": 28, "average": 20}
    },
    "interaction_rate": {"excellent": 9, "good": 5, "average": 3},
    "fan_rate": {"excellent": 2.8, "good": 1.4, "average": 0.6},
    "optimal_time": ["08:00-09:00", "12:00-13:00", "20:00-21:00"]
  },
  "健身": {
    "avg_views": 8000,
    "completion_rate": {
      "60s": {"excellent": 48, "good": 38, "average": 28},
      "180s": {"excellent": 40, "good": 30, "average": 22}
    },
    "interaction_rate": {"excellent": 10, "good": 5.5, "average": 3.5},
    "fan_rate": {"excellent": 3.5, "good": 1.8, "average": 0.8},
    "optimal_time": ["06:00-07:00", "19:00-21:00"]
  },
  "穿搭": {
    "avg_views": 10000,
    "completion_rate": {
      "30s": {"excellent": 52, "good": 42, "average": 32},
      "60s": {"excellent": 46, "good": 36, "average": 26}
    },
    "interaction_rate": {"excellent": 11, "good": 6, "average": 4},
    "fan_rate": {"excellent": 3.2, "good": 1.6, "average": 0.7},
    "optimal_time": ["12:00-13:00", "20:00-22:00"]
  },
  "娱乐": {
    "avg_views": 15000,
    "completion_rate": {
      "30s": {"excellent": 60, "good": 50, "average": 40},
      "60s": {"excellent": 55, "good": 45, "average": 35}
    },
    "interaction_rate": {"excellent": 15, "good": 8, "average": 5},
    "fan_rate": {"excellent": 2, "good": 1, "average": 0.4},
    "optimal_time": ["12:00-13:00", "21:00-23:00"]
  },
  "母婴": {
    "avg_views": 7000,
    "completion_rate": {
      "60s": {"excellent": 44, "good": 34, "average": 26},
      "180s": {"excellent": 38, "good": 28, "average": 20}
    },
    "interaction_rate": {"excellent": 12, "good": 6.5, "average": 4},
    "fan_rate": {"excellent": 4, "good": 2, "average": 0.9},
    "optimal_time": ["10:00-11:00", "14:00-15:00", "21:00-22:00"]
  }
}
```

---

## 二、标题公式库 (title_formulas.json)

```json
{
  "标题公式": {
    "数字型": [
      "学会这{n}招，快速搞定{topic}",
      "{n}个{topic}技巧，学会了你就是高手",
      "只要{n}分钟，轻松掌握{topic}",
      "关于{topic}，你需要知道的{n}件事",
      "{n}年经验总结的{topic}方法"
    ],
    "疑问型": [
      "为什么你的{topic}总是不成功？",
      "{topic}到底难在哪里？",
      "你的{topic}方法是对的吗？",
      "怎么做{topic}才有效？",
      "为什么别人{topic}那么容易？"
    ],
    "悬念型": [
      "原来{topic}这么简单，后悔现在才知道",
      "这个{topic}秘密，99%的人不知道",
      "没想到{topic}还能这样操作",
      "{topic}的真相，让你大开眼界",
      "学会了{topic}，生活完全不一样"
    ],
    "感叹型": [
      "太绝了！{topic}竟然这么简单",
      "天呐！{topic}原来这么简单",
      "绝了！用了这个方法，{topic}轻松搞定",
      "太牛了！这个{topic}技巧太管用了",
      "OMG！{topic}这样做效果翻倍"
    ],
    "痛点型": [
      "还在为{topic}烦恼？试试这个方法",
      "{topic}问题多？可能是你方法不对",
      "你还在为{topic}发愁吗？",
      "{topic}做不好？看完你就知道了",
      "总是{topic}？多半是没找对方法"
    ],
    "利益型": [
      "学会这个方法，{topic}效率翻倍",
      "这个技巧让你的{topic}效率提升10倍",
      "快速搞定{topic}，只需这一招",
      "手把手教你{topic}，一看就会",
      "零基础也能学会的{topic}方法"
    ],
    "反差型": [
      "别人都{common}，只有我{unique}",
      "同样{topic}，为什么差距这么大？",
      "同样是{topic}，效果差距不是一点点",
      "为什么你总是{common}？看完就明白了",
      "别人不知道的{topic}秘密"
    ],
    "从众型": [
      "{percent}%的人都不知道的{topic}方法",
      "看过这个{topic}方法的，都收藏了",
      "全网都在用的{topic}技巧",
      "{many}万人都在学的{topic}方法",
      "这个{topic}方法，让{many}人受益"
    ],
    "身份型": [
      "{identity}必看的{topic}攻略",
      "作为一个{identity}，{topic}必须了解",
      "{identity}都在用的{topic}方法",
      "给{identity}的{topic}建议",
      "{identity}应该如何{topic}？"
    ],
    "时间型": [
      "{time}学会{topic}，你也可以",
      "每天{timing}，一个月后{topic}完全不一样",
      "{time}搞定{topic}，效率翻倍",
      "坚持{time}，你的{topic}会有惊人变化",
      "{time}学会{topic}，终身受用"
    ]
  },
  "公式参数": {
    "n": ["3", "5", "7", "10", "99%"],
    "topic": ["高效学习", "职场沟通", "时间管理", "减肥", "护肤"],
    "common": ["做不好", "失败", "放弃", "焦虑", "迷茫"],
    "unique": ["成功了", "突破", "逆袭", "成长", "进步"],
    "identity": ["职场人", "新手妈妈", "学生党", "打工人", "考证党"],
    "time": ["7天", "21天", "30天", "100天"],
    "timing": ["早起", "每天10分钟", "坚持一个月"],
    "many": ["10万", "100万", "1000万"],
    "percent": ["90", "95", "99"]
  },
  "适用场景": {
    "数字型": "教程、干货、技巧类内容",
    "疑问型": "科普、解惑、揭秘类内容",
    "感叹型": "好物、效果、惊艳类内容",
    "悬念型": "揭秘、反转、秘密类内容",
    "痛点型": "问题、困扰、解决方案类内容",
    "利益型": "效率、方法、捷径类内容",
    "反差型": "对比、PK、对比类内容",
    "从众型": "推荐、热门、必学类内容",
    "身份型": "定向人群、精准受众类内容",
    "时间型": "周期改变、习惯养成类内容"
  }
}
```

---

## 三、热门话题数据 (hot_topics.json)

```json
{
  "更新时间": "2024-05-15",
  "抖音热榜": [
    {"rank": 1, "topic": "#春季穿搭灵感", "heat": 9856000, "trend": "up"},
    {"rank": 2, "topic": "#打工人的周一早餐", "heat": 8523000, "trend": "up"},
    {"rank": 3, "topic": "#居家健身30天挑战", "heat": 7632000, "trend": "down"},
    {"rank": 4, "topic": "#职场沟通技巧", "heat": 6541000, "trend": "up"},
    {"rank": 5, "topic": "#美食探店打卡", "heat": 5987000, "trend": "stable"},
    {"rank": 6, "topic": "#美妆新品测评", "heat": 5432000, "trend": "up"},
    {"rank": 7, "topic": "#存钱打卡计划", "heat": 4876000, "trend": "up"},
    {"rank": 8, "topic": "#读书分享", "heat": 4321000, "trend": "down"},
    {"rank": 9, "topic": "#宠物日常", "heat": 3987000, "trend": "stable"},
    {"rank": 10, "topic": "#新手摄影教程", "heat": 3562000, "trend": "up"}
  ],
  "行业热点": {
    "美食": ["家常菜", "甜点", "饮品", "探店", "打卡"],
    "美妆": ["早C晚A", "成分党", "平替", "素颜霜", "新品发布"],
    "知识": ["Excel技巧", "设计教程", "摄影技巧", "求职干货"],
    "职场": ["职场沟通", "加薪技巧", "同事关系", "工作效率"],
    "健身": ["减脂餐", "马甲线", "居家健身", "瑜伽"],
    "穿搭": ["春季穿搭", "显高", "显白", "学生党"]
  },
  "节日节点": {
    "5月": [
      {"date": "5.1-5.3", "name": "劳动节", "topic": "劳动节特别内容"},
      {"date": "5.4", "name": "青年节", "topic": "青年节热点"},
      {"date": "5.11", "name": "母亲节", "topic": "母亲节特别"},
      {"date": "5.20", "name": "520", "topic": "表白日/情侣内容"}
    ],
    "6月": [
      {"date": "6.1", "name": "儿童节", "topic": "儿童节内容"},
      {"date": "6.18", "name": "618", "topic": "电商大促"},
      {"date": "6.22", "name": "端午节", "topic": "端午节特别"}
    ]
  }
}
```

---

## 四、账号数据模板 (account_data.json)

```json
{
  "账号信息": {
    "账号名称": "",
    "账号ID": "",
    "行业": "",
    "粉丝数": 0,
    "注册时间": "",
    "变现方向": ""
  },
  "人设信息": {
    "头像": {"是否清晰": true, "是否专业": true},
    "昵称": {"是否好记": true, "是否有关联": true},
    "简介": {"是否说清价值": true, "是否引导关注": true},
    "内容": {"是否统一风格": true, "是否有人设": true},
    "语言风格": {"是否一致": true}
  },
  "数据指标": {
    "平均播放": 0,
    "完播率": "0%",
    "互动率": "0%",
    "转粉率": "0%",
    "篇均点赞": 0,
    "篇均评论": 0
  },
  "粉丝画像": {
    "性别分布": {"男": "0%", "女": "0%"},
    "年龄分布": {"18-24": "0%", "25-35": "0%", "35+": "0%"},
    "地域TOP5": [],
    "活跃时段": []
  },
  "内容分类": {
    "教程类": {"占比": "0%", "平均播放": 0},
    "测评类": {"占比": "0%", "平均播放": 0},
    "剧情类": {"占比": "0%", "平均播放": 0},
    "日常类": {"占比": "0%", "平均播放": 0}
  },
  "发布习惯": {
    "更新频率": "每周X条",
    "固定发布时间": [],
    "内容来源": []
  }
}
```

---

## 五、竞品监控模板 (competitor_data.json)

```json
{
  "监控周期": "近30天",
  "竞品列表": [
    {
      "账号名称": "",
      "账号ID": "",
      "粉丝数": 0,
      "近7天涨粉": 0,
      "近7天爆款": [],
      "更新频率": 0,
      "内容方向": [],
      "互动率": "0%",
      "值得学习点": []
    }
  ],
  "监控记录": [
    {
      "日期": "",
      "记录人": "",
      "竞品动态": [],
      "启发": []
    }
  ]
}
```

---

## 六、直播话术库 (live_scripts.json)

```json
{
  "开场话术": {
    "暖场": [
      "欢迎{username}进入直播间！（读名字）感谢关注！",
      "刚进来的小伙伴打个招呼～今天直播间有{benefit}，先别走开！",
      "欢迎{username}，你是第{count}个进来的，太给力了！"
    ],
    "价值预告": [
      "今天给大家带来{count}款{product}，{benefit}！",
      "直播间专属价，只有今天有！错过不再来！",
      "今天准备了很多{product}，保证让你们买到赚到！"
    ],
    "互动": [
      "刚进来的扣个1，让我看看有多少人！",
      "觉得今天福利可以的扣666！",
      "想要{product}的扣想要！"
    ]
  },
  "产品话术": {
    "痛点引入": [
      "你们是不是也有{problem}的烦恼？",
      "之前很多粉丝问我，{problem}怎么办？",
      "今天就给你们解决{problem}这个问题！"
    ],
    "卖点讲解": [
      "第一，{feature1}，解决你的{problem1}！",
      "第二，{feature2}，{benefit2}！",
      "第三，{feature3}，现在下单还送{gift}！"
    ],
    "价格包装": [
      "官方价{original_price}，今天直播间专属价只要{price}！",
      "今天不要{original_price}，也不要{price}，只要{final_price}！"
    ]
  },
  "促单话术": {
    "紧迫感": [
      "库存只剩{count}件了！",
      "价格只限今天直播间！",
      "这波福利结束就没了！"
    ],
    "限量": [
      "每个ID限购{count}件！",
      "今天只准备了{count}份！抢完为止！"
    ],
    "福利": [
      "拍2件送{gift1}，拍3件送{gift2}！",
      "现在下单的粉丝额外送{gift}！"
    ],
    "从众": [
      "已经{count}人下单了！",
      "刚才那个姐姐一下拍了{count}件！"
    ]
  },
  "互动话术": {
    "抽奖": [
      "点赞到{count}抽{gift}！",
      "关注主播参与抽奖，{gift}免费送！"
    ],
    "问答": [
      "有什么问题打在公屏上！",
      "{question}问得最多，给大家统一回复..."
    ],
    "引导": [
      "帮主播点点关注，下期更精彩！",
      "加入粉丝团还有{gift}送！"
    ]
  },
  "感谢话术": [
    "感谢{count}位来到直播间！",
    "感谢{username}的关注！",
    "今天的直播就到这里，下期见！",
    "拜拜～记得点关注不迷路！"
  ]
}
```
