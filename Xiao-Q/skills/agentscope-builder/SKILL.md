\---

name: agentscope-builder
description: 严格依据 AgentScope 官方文档与 CoPaw 工程实现模式，指导基于 AgentScope v1.0 搭建单智能体、多智能体、工具、记忆、计划与技能系统。
tags:

* agentscope
* react-agent
* toolkit
* memory
* plan
* pipeline
* copaw

\---

# AgentScope 智能体搭建技能

## 这个技能的目标

当用户要求你基于 AgentScope 框架搭建、改造或扩展智能体时，你必须：

1. **优先遵循 AgentScope 官方文档中的类名、参数名、调用顺序和工程抽象**。
2. **在工程实现层面参考 CoPaw 的落地方式**，尤其是：`ReActAgent` 封装、动态技能加载、工作区提示词拼装、内存/钩子扩展、按目录组织能力。
3. 输出内容必须尽量是**可运行代码 + 明确目录结构 + 关键设计说明**，避免只给概念。

\---

## 硬性规则

### 1\. API 使用规则

* 只能使用 AgentScope 官方文档中出现过或与其一致的 API 形式。
* 默认单智能体实现优先使用 `ReActAgent`。
* `model` 与 `formatter` 必须匹配，不能混搭。
* 工具统一通过 `Toolkit` 注册。
* 技能统一通过目录中的 `SKILL.md` 表达，并通过 `Toolkit.register\\\_agent\\\_skill()` 注册。
* 短期记忆优先从 `InMemoryMemory()` 起步；确有持久化需要时，再升级到 SQLAlchemy / Redis / Tablestore 等实现。
* 复杂任务优先考虑 `PlanNotebook`，多智能体编排优先考虑官方 `pipeline`。

### 2\. 输出代码规则

* 优先输出 **Python 3.10+** 代码。
* 优先输出 **异步写法**，因为官方示例大量采用 `async` / `await`。
* 必须给出完整 `import`。
* 若用户没有指定模型厂商，优先给出“**官方最小可运行骨架** + 模型替换说明”。
* 若用户要求 OpenAI 兼容接口或 vLLM，自定义模型接入时要明确说明：使用 `OpenAIChatModel`，并通过 `client\\\_kwargs={"base\\\_url": ...}` 指定兼容端点。

### 3\. 架构规则

生成方案时，默认采用如下分层：

* **model layer**：模型与 formatter 绑定
* **tool layer**：`Toolkit` 统一注册工具
* **memory layer**：短期记忆 / 长期记忆 / 检索入口
* **agent layer**：`ReActAgent` 或其封装类
* **workflow layer**：计划、顺序管道、扇出管道、多智能体路由
* **skill layer**：技能目录与 `SKILL.md`
* **workspace layer**：系统提示文件、技能目录、会话状态文件

\---

## AgentScope 官方推荐的理解顺序

在 AgentScope 中，**智能体、记忆、长期记忆和工具模块本身都是有状态对象**。因此，设计时要把“对象初始化”和“状态恢复/迁移”分开考虑。消息 `Msg` 是统一数据结构，贯穿用户输入、智能体对话、工具调用、记忆存储与多智能体协作。

建议按以下顺序搭建：

1. 安装 AgentScope
2. 理解 `Msg`
3. 选定模型与 formatter
4. 定义工具并注册到 `Toolkit`
5. 创建 `ReActAgent`
6. 接入 `memory`
7. 需要复杂任务时接 `PlanNotebook`
8. 需要多智能体时接 `pipeline`
9. 需要复用专业能力时接 `register\\\_agent\\\_skill`

\---

## 官方最小实现模板

## 1\. 安装

```bash
pip install agentscope

# 如需额外模型/工具能力：
# Windows
pip install agentscope\\\[full]

# macOS / Linux
pip install agentscope\\\\\\\[full\\\\]
```

\---

## 2\. 消息对象写法

`Msg` 的核心字段是：

* `name`
* `role`
* `content`
* `metadata`

其中：

* `role` 只能是 `system` / `assistant` / `user`
* `content` 可以是纯字符串，也可以是内容块列表
* `metadata` 适合承载结构化输出，不参与常规提示拼接

```python
from agentscope.message import Msg

user\\\_msg = Msg(
    name="user",
    role="user",
    content="请先分析需求，再给出 AgentScope 工程结构。",
)
```

\---

## 3\. 模型与 formatter

### 强制要求

* `ReActAgent` 创建时，`model` 与 `formatter` 必须一起确定。
* 若是 OpenAI 兼容模型，优先使用 `OpenAIChatModel`。
* 模型生成参数通过 `generate\\\_kwargs` 传入。

### 官方风格最小示例（DashScope）

```python
import os
from agentscope.model import DashScopeChatModel
from agentscope.formatter import DashScopeChatFormatter

model = DashScopeChatModel(
    model\\\_name="qwen-max",
    api\\\_key=os.environ\\\["DASHSCOPE\\\_API\\\_KEY"],
    stream=True,
    enable\\\_thinking=False,
)

formatter = DashScopeChatFormatter()
```

### OpenAI 兼容接口写法要点

如果用户使用 OpenAI 兼容服务（例如 vLLM、自建网关等），按下面的思路写：

```python
from agentscope.model import OpenAIChatModel
from agentscope.formatter import OpenAIChatFormatter

model = OpenAIChatModel(
    client\\\_kwargs={"base\\\_url": "http://localhost:8000/v1"},
    generate\\\_kwargs={"temperature": 0.2, "max\\\_tokens": 1200},
)

formatter = OpenAIChatFormatter()
```

> 注意：这里展示的是官方文档明确提到的 `client\\\_kwargs` 与 `generate\\\_kwargs` 用法；若用户有既定 provider 配置，再按其环境补足 `model\\\_name`、`api\\\_key` 等参数。

\---

## 4\. 工具函数与 Toolkit

AgentScope 中工具函数应满足两点：

* 有清晰 docstring，便于自动解析参数说明
* 返回 `ToolResponse`，或返回 `ToolResponse` 的生成器

### 最小工具示例

```python
from agentscope.message import TextBlock
from agentscope.tool import ToolResponse


def project\\\_search(query: str) -> ToolResponse:
    """在项目知识中搜索信息。

    Args:
        query (str): 搜索关键词。
    """
    return ToolResponse(
        content=\\\[
            TextBlock(
                type="text",
                text=f"已收到搜索请求：{query}",
            ),
        ],
    )
```

### 注册工具

```python
from agentscope.tool import Toolkit

toolkit = Toolkit()
toolkit.register\\\_tool\\\_function(project\\\_search)
```

### 什么时候加工具组

如果一个能力域下有多组工具（例如浏览器工具、数据库工具、文件系统工具），再使用 `Toolkit.create\\\_tool\\\_group()` 做显式管理；否则直接注册到默认组即可。

\---

## 5\. 创建 ReActAgent

官方文档里，`ReActAgent` 常用参数包括：

* `name`
* `sys\\\_prompt`
* `model`
* `formatter`
* `toolkit`
* `memory`
* `long\\\_term\\\_memory`
* `long\\\_term\\\_memory\\\_mode`
* `enable\\\_meta\\\_tool`
* `parallel\\\_tool\\\_calls`
* `max\\\_iters`
* `plan\\\_notebook`

### 官方风格单智能体最小模板

```python
import asyncio
import os

from agentscope.agent import ReActAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.model import DashScopeChatModel
from agentscope.tool import Toolkit
from agentscope.message import TextBlock, Msg
from agentscope.tool import ToolResponse


def execute\\\_plan(topic: str) -> ToolResponse:
    """根据主题返回一个简要执行计划。

    Args:
        topic (str): 任务主题。
    """
    return ToolResponse(
        content=\\\[
            TextBlock(
                type="text",
                text=f"建议先拆解任务，再检索资料，最后生成结果：{topic}",
            ),
        ],
    )


async def main() -> None:
    toolkit = Toolkit()
    toolkit.register\\\_tool\\\_function(execute\\\_plan)

    agent = ReActAgent(
        name="Jarvis",
        sys\\\_prompt="你是一个严格遵循 AgentScope 官方用法的开发助手。",
        model=DashScopeChatModel(
            model\\\_name="qwen-max",
            api\\\_key=os.environ\\\["DASHSCOPE\\\_API\\\_KEY"],
            stream=True,
            enable\\\_thinking=False,
        ),
        formatter=DashScopeChatFormatter(),
        toolkit=toolkit,
        memory=InMemoryMemory(),
        max\\\_iters=10,
    )

    reply = await agent(
        Msg(name="user", role="user", content="帮我设计一个智能客服 Agent。")
    )
    print(reply)


if \\\_\\\_name\\\_\\\_ == "\\\_\\\_main\\\_\\\_":
    asyncio.run(main())
```

\---

## 6\. 记忆接入策略

### 短期记忆

默认从 `InMemoryMemory()` 起步。它简单、官方示例使用频繁，并且适合先跑通功能。

### 标记（mark）

AgentScope 的记忆支持给消息打 `mark`，这对于：

* 一次性提示
* 中间态信息
* 可删除的系统 hint
* 不同来源的上下文分层

都很有帮助。

### 长期记忆模式

如果用户明确需要长期记忆，优先解释三种模式：

* `agent\\\_control`：让智能体借助工具主动管理长期记忆
* `static\\\_control`：在回复前后自动做检索/写入
* `both`：两者同时启用

### 建议

* 第一版：`InMemoryMemory()` 即可
* 第二版：若要跨会话保留上下文，再接持久化 memory
* 第三版：若要让智能体主动查询历史，再补 memory-search 工具

\---

## 7\. 计划（PlanNotebook）接入规则

只要任务具有明显的“拆解—执行—回收”结构，就考虑启用 `PlanNotebook`。

适合场景：

* 研究型问答
* 报告生成
* 代码迁移
* 多步数据处理
* 长链路自动化任务

不适合场景：

* 一轮即可完成的简单问答
* 纯聊天
* 明显不需要拆任务的操作

### 接入思路

```python
from agentscope.plan import PlanNotebook

plan\\\_notebook = PlanNotebook(max\\\_subtasks=8)

agent = ReActAgent(
    name="Planner",
    sys\\\_prompt="你需要先拆解任务，再逐步完成。",
    model=model,
    formatter=formatter,
    toolkit=toolkit,
    memory=InMemoryMemory(),
    plan\\\_notebook=plan\\\_notebook,
)
```

> 官方文档强调：当前计划模块默认是\\\*\\\*顺序执行子任务\\\*\\\*，不是任意 DAG 调度器。因此不要先假设并行子任务编排。

\---

## 8\. 多智能体编排优先级

当用户要多智能体时，优先从官方 `pipeline` 起步，而不是先写自定义 orchestrator。

### 顺序管道

适合：

* 需求分析 Agent → 实现 Agent → 审查 Agent
* 检索 Agent → 总结 Agent → 输出 Agent

```python
from agentscope.pipeline import sequential\\\_pipeline

msg = await sequential\\\_pipeline(
    agents=\\\[analyst\\\_agent, builder\\\_agent, reviewer\\\_agent],
    msg=None,
)
```

### 扇出管道

适合：

* 同一问题交给多个专家 Agent 并行给意见
* 多个候选答案后再聚合

如果用户只是要“多个角色协作”，默认先给顺序管道方案；只有明确要并发多视角时，再给 fanout。

\---

## 9\. 智能体技能（Agent Skill）接入方式

AgentScope 原生支持把“技能目录”挂到 `Toolkit` 上。技能本质上是**目录 + `SKILL.md`**，然后由 `Toolkit.register\\\_agent\\\_skill()` 注册。

### 官方接入步骤

```python
from agentscope.tool import Toolkit

toolkit = Toolkit()
toolkit.register\\\_agent\\\_skill("sample\\\_skill")

agent\\\_skill\\\_prompt = toolkit.get\\\_agent\\\_skill\\\_prompt()
print(agent\\\_skill\\\_prompt)
```

### 技能目录最小结构

```text
my\\\_skill/
└── SKILL.md
```

### `SKILL.md` 最小模板

```markdown
---
name: my\\\_skill
description: 用于指导 Agent 按固定流程完成某类任务。
---

# 使用说明

当用户要求你处理某类任务时，先阅读本文件，再按约定流程执行。
```

### 什么时候用 Agent Skill

* 一类任务会反复出现
* 仅靠 system prompt 不够稳定
* 需要把流程、规则、注意事项、目录约束写清楚
* 需要把某种“专业操作范式”长期沉淀下来

\---

## CoPaw 实现模式：你应该借鉴什么

CoPaw 不是在 AgentScope 之上“另起炉灶”，而是把 AgentScope 的核心抽象进一步工程化。搭建你自己的系统时，优先借鉴以下几点。

## 1\. 用自定义 Agent 类封装 `ReActAgent`

CoPaw 的主 Agent 继承自 `ReActAgent`，初始化顺序非常值得参考：

1. 创建 `Toolkit`
2. 注册内置工具
3. 注册技能目录
4. 构造系统提示
5. 创建 model + formatter
6. 调用 `super().\\\_\\\_init\\\_\\\_(...)`
7. 再接 memory manager、命令处理器、hooks

### 推荐仿写模板

```python
from agentscope.agent import ReActAgent
from agentscope.memory import InMemoryMemory
from agentscope.tool import Toolkit


class ProjectAgent(ReActAgent):
    def \\\_\\\_init\\\_\\\_(self, model, formatter, sys\\\_prompt: str):
        toolkit = Toolkit()
        toolkit.register\\\_tool\\\_function(project\\\_search)
        toolkit.register\\\_agent\\\_skill("./skills/agentscope\\\_builder")

        super().\\\_\\\_init\\\_\\\_(
            name="ProjectAgent",
            model=model,
            formatter=formatter,
            sys\\\_prompt=sys\\\_prompt,
            toolkit=toolkit,
            memory=InMemoryMemory(),
            max\\\_iters=12,
        )
```

这比把所有逻辑直接塞进 `main.py` 更适合后续扩展。

\---

## 2\. 按工作区文件构造系统提示

CoPaw 会从工作区中的多个 Markdown 文件拼装系统提示，核心思路是：

* 把“角色设定”拆到独立文件
* 启动时拼装，而不是全部硬编码在 Python 字符串里

可借鉴的文件分层：

* `AGENTS.md`：职责、行为边界、执行原则
* `SOUL.md`：语气、风格、人格偏好
* `PROFILE.md`：业务背景、常量、领域知识

### 建议

* 把会经常改动的系统提示搬到 Markdown 文件
* Python 只负责“读取 + 拼装”
* 这样更方便多智能体分别定制人格与能力边界

\---

## 3\. 技能目录不要散落，统一挂到工作区

CoPaw 的技能实践说明了两件事：

* **技能本体应该是目录**，而不是只是一段 prompt
* **技能启用状态应与运行时配置解耦**

建议你采用以下目录：

```text
project/
├── app/
│   ├── main.py
│   ├── agent\\\_factory.py
│   ├── prompts/
│   │   ├── AGENTS.md
│   │   ├── SOUL.md
│   │   └── PROFILE.md
│   ├── tools/
│   │   ├── search.py
│   │   └── file\\\_ops.py
│   └── workflows/
│       ├── single\\\_agent.py
│       └── multi\\\_agent.py
├── skills/
│   ├── agentscope\\\_builder/
│   │   └── SKILL.md
│   └── report\\\_writer/
│       └── SKILL.md
└── data/
```

如果你要做“多技能启停”，可以再加一个 manifest 文件维护：

* 是否启用
* 哪些 channel / 场景可见
* 是否需要外部环境变量

\---

## 4\. 技能文档必须有 front matter

CoPaw 的文档与实现都表明，`SKILL.md` 最少要包含 front matter 中的：

* `name`
* `description`

因此，当你帮用户创建技能文档时，默认带上 YAML front matter，不要只写正文。

### 推荐模板

```markdown
---
name: skill\\\_name
description: 这个技能解决什么问题、在什么场景下启用。
---

# 任务边界

# 操作步骤

# 输出要求

# 禁止事项
```

\---

## 5\. 用“工具 + 技能 + 提示词文件”三层分工

参考 CoPaw，建议这样分工：

### 工具（Tool）负责

* 真实执行
* 访问外部系统
* 文件读写
* Shell / Browser / API / DB 调用

### 技能（Skill）负责

* 告诉 Agent 什么时候用什么工具
* 规定步骤、策略、限制与输出标准
* 固化某类任务的方法论

### 系统提示（Prompt files）负责

* 角色
* 目标
* 风格
* 全局约束

不要把三者混成一个超长 system prompt。

\---

## 6\. 钩子（hook）适合做“运行时治理”

CoPaw 会在 Agent 初始化后追加 hook，用于：

* 首次启动引导
* 上下文压缩
* 运行前检查

当用户要求以下能力时，你应优先建议 hook：

* “每轮推理前检查上下文长度”
* “首次运行时先读一份 bootstrap 文档”
* “执行前自动注入 hint”
* “超长历史自动压缩”

如果只是普通工具调用，不需要引入 hook。

\---

## 推荐回答模板

当用户要求“帮我搭一个 AgentScope 智能体”时，优先按下面格式输出：

### A. 先给架构

* 这是单智能体还是多智能体
* 是否需要工具
* 是否需要记忆
* 是否需要计划
* 是否需要技能目录

### B. 再给目录结构

* `main.py`
* `agent\\\_factory.py`
* `tools/`
* `skills/`
* `prompts/`

### C. 再给最小可运行代码

* 模型 + formatter
* toolkit + tool
* agent
* `asyncio.run(main())`

### D. 最后给扩展路线

* 从 `InMemoryMemory` 升级到持久化 memory
* 从单 Agent 升级到 pipeline
* 从内置规则升级到 skill 目录
* 从固定 prompt 升级到工作区 Markdown 提示文件

\---

## 常见正确做法

### 场景 1：用户说“帮我做一个能调工具的单智能体”

你应该：

* 直接给 `ReActAgent`
* 给一个 `Toolkit`
* 至少注册一个工具函数
* 用 `InMemoryMemory()`
* 给最小运行入口

### 场景 2：用户说“帮我做一个研究型 Agent”

你应该：

* 在单智能体基础上补 `PlanNotebook`
* 给检索工具
* 给结果汇总工具或输出约束
* 必要时再加 skill

### 场景 3：用户说“我要多个角色协作”

你应该：

* 先问清是顺序协作还是并行协作
* 若未说明，先给 `sequential\\\_pipeline`
* 若需要多专家并发，再给 fanout

### 场景 4：用户说“我要长期复用一套搭建规范”

你应该：

* 直接产出 `SKILL.md`
* front matter 带 `name` 与 `description`
* 把“什么时候用、怎么做、输出要求、禁止事项”写清楚

\---

## 明确避免的做法

* 不要臆造 `AgentScope.init()` 之类官方文档没有的入口
* 不要把 OpenAI 兼容模型与 Anthropic formatter 混用
* 不要把所有业务逻辑都塞进一个 system prompt
* 不要在还没需要持久化时就把 memory 设计得过重
* 不要用户只要单智能体时就一上来设计复杂多 Agent 调度器
* 不要把 skill 写成“只有描述、没有使用规则”的空文档
* 不要忘记为工具写 docstring
* 不要给出缺 import、缺入口、不可运行的碎片代码

\---

## 一份更适合实战的项目脚手架

```text
agentscope\\\_project/
├── main.py
├── requirements.txt
├── app/
│   ├── agent\\\_factory.py
│   ├── prompts/
│   │   ├── AGENTS.md
│   │   ├── SOUL.md
│   │   └── PROFILE.md
│   ├── tools/
│   │   ├── project\\\_search.py
│   │   ├── file\\\_tool.py
│   │   └── web\\\_tool.py
│   ├── skills/
│   │   └── agentscope\\\_builder/
│   │       └── SKILL.md
│   ├── memory/
│   │   └── memory\\\_factory.py
│   └── workflows/
│       ├── single\\\_agent.py
│       ├── planner\\\_agent.py
│       └── multi\\\_agent\\\_pipeline.py
└── data/
```

\---

## 当你使用本技能时，你应该怎么做

当用户给出需求后，你应按下面流程执行：

1. 判断是单智能体、多智能体、研究型 Agent、流程型 Agent，还是技能文档需求。
2. 从官方抽象里选择：`ReActAgent` / `Toolkit` / `InMemoryMemory` / `PlanNotebook` / `pipeline` / `register\\\_agent\\\_skill`。
3. 若用户要求工程化实现，则套用 CoPaw 风格：

   * 自定义 Agent 类
   * 工作区 prompt 文件
   * skills 目录
   * hooks / memory 扩展
4. 输出：

   * 目录结构
   * 完整代码
   * 为什么这样设计
   * 下一步怎么扩展

\---

## 参考来源

### AgentScope 官方文档

* 中文文档首页：[https://doc.agentscope.io/zh\_CN/index.html](https://doc.agentscope.io/zh_CN/index.html)
* 安装：[https://doc.agentscope.io/zh\_CN/tutorial/quickstart\_installation.html](https://doc.agentscope.io/zh_CN/tutorial/quickstart_installation.html)
* 核心概念：[https://doc.agentscope.io/zh\_CN/tutorial/quickstart\_key\_concept.html](https://doc.agentscope.io/zh_CN/tutorial/quickstart_key_concept.html)
* 创建消息：[https://doc.agentscope.io/zh\_CN/tutorial/quickstart\_message.html](https://doc.agentscope.io/zh_CN/tutorial/quickstart_message.html)
* 创建 ReAct 智能体：[https://doc.agentscope.io/zh\_CN/tutorial/quickstart\_agent.html](https://doc.agentscope.io/zh_CN/tutorial/quickstart_agent.html)
* 模型：[https://doc.agentscope.io/zh\_CN/tutorial/task\_model.html](https://doc.agentscope.io/zh_CN/tutorial/task_model.html)
* 工具：[https://doc.agentscope.io/zh\_CN/tutorial/task\_tool.html](https://doc.agentscope.io/zh_CN/tutorial/task_tool.html)
* 记忆：[https://doc.agentscope.io/zh\_CN/tutorial/task\_memory.html](https://doc.agentscope.io/zh_CN/tutorial/task_memory.html)
* 计划：[https://doc.agentscope.io/zh\_CN/tutorial/task\_plan.html](https://doc.agentscope.io/zh_CN/tutorial/task_plan.html)
* 管道：[https://doc.agentscope.io/zh\_CN/tutorial/task\_pipeline.html](https://doc.agentscope.io/zh_CN/tutorial/task_pipeline.html)
* 智能体技能：[https://doc.agentscope.io/zh\_CN/tutorial/task\_agent\_skill.html](https://doc.agentscope.io/zh_CN/tutorial/task_agent_skill.html)

### CoPaw 参考实现

* 仓库主页：[https://github.com/agentscope-ai/CoPaw](https://github.com/agentscope-ai/CoPaw)
* `src/copaw/agents/react\\\_agent.py`
* `src/copaw/agents/model\\\_factory.py`
* `src/copaw/agents/skills\\\_manager.py`
* `src/copaw/agents/prompt.py`
* `src/copaw/agents/skills/`
* 技能说明文档：[https://copaw.agentscope.io/docs/skills/](https://copaw.agentscope.io/docs/skills/)
* 配置与工作目录：[https://copaw.agentscope.io/docs/config/](https://copaw.agentscope.io/docs/config/)

