# FlowSight Dataset — 论文配图（Mermaid 源码）

本文件收录用于论文写作的所有流程图 / 结构图的 Mermaid 源码。
渲染时直接复制对应代码块到 [mermaid.live](https://mermaid.live) 或 Obsidian / Typora 预览即可。

---

## Fig 1 · 数据集整体结构

> 读者第一眼看到的总览图。强调三大来源（真实 / 拟真合成 / 无意义合成）及其在数据集中的比例与作用，同时标注每条样本的统一"三件套"格式。

```mermaid
graph TD
    DS[("FlowSight Dataset\n1 000 条")]

    DS --> REAL["🗂 真实数据\n500 条\n来自 GitHub 开源项目"]
    DS --> SYN["🤖 合成数据\n500 条\nLLM 生成"]

    SYN --> MEAN["拟真合成\n200 条\n逻辑合理·术语正常"]
    SYN --> NONE["无意义合成\n300 条\n用于探测"看图"能力"]

    NONE --> CHAOS["Chaos（完全混乱）\n150 条\n随机节点·荒谬组合\n常识无法帮助作答"]
    NONE --> MISLED["Misleading（误导）\n150 条\n有真实对应但故意组合错误\n常识反而会误导"]

    REAL --> ITEM["每条样本\ndiagram.mmd\ndiagram.png\ndescription.txt"]
    MEAN --> ITEM
    CHAOS --> ITEM
    MISLED --> ITEM

    ITEM --> QA["qa.json\n6 道单选题\nfactual / reasoning / negation\neasy / medium / hard"]

    style DS fill:#f0f4ff,stroke:#6c8ebf,stroke-width:2px
    style REAL fill:#d5e8d4,stroke:#82b366
    style SYN fill:#fff2cc,stroke:#d6b656
    style MEAN fill:#ffe6cc,stroke:#d79b00
    style NONE fill:#f8cecc,stroke:#b85450
    style CHAOS fill:#f8cecc,stroke:#b85450
    style MISLED fill:#f8cecc,stroke:#b85450
    style ITEM fill:#dae8fc,stroke:#6c8ebf
    style QA fill:#e1d5e7,stroke:#9673a6
```

---

## Fig 2 · 真实数据采集与标注工作流

> 以"搜索词驱动"为入口，展示从 GitHub 检索到最终一条样本入库的完整路径。两层过滤（规则 + AI 质检）和渲染失败的丢弃路径要清楚。人工审查以侧注方式标注。

```mermaid
flowchart TD
    Q["🔍 GitHub 搜索\n40+ 组关键词\n(mermaid + 领域词)"]

    Q --> R["按 Star 数排序\n候选仓库列表"]

    R --> DOC["抓取 README / 文档\n提取 Mermaid 代码块"]

    DOC --> RULE{"规则过滤\n行数 ≥ 6\n连线数 ≥ 3\n标签有意义?"}
    RULE -- 不通过 --> DROP1["❌ 丢弃"]
    RULE -- 通过 --> HASH{"结构哈希去重\n(节点边集合)"}

    HASH -- 重复 --> DROP2["❌ 去重丢弃"]
    HASH -- 新样本 --> AI{"🤖 AI 质检\nGemini 判断\n是否真实业务图?"}
    AI -- 否 --> DROP3["❌ 丢弃"]
    AI -- 是 --> RENDER["mermaid.ink\n渲染 PNG"]
    RENDER -- 失败 --> DROP4["❌ 渲染失败丢弃"]
    RENDER -- 成功 --> DESC["生成 Description\n多模态 LLM\n结合 README / 仓库上下文"]
    DESC --> META["写入 metadata.json\n记录来源仓库 · 星数 · 行数"]

    HQ(["👤 人工抽检\n验证质量与多样性"])
    AI -. 支持 .-> HQ
    DESC -. 支持 .-> HQ

    META --> DONE["✅ 入库\n500 条真实样本"]

    style Q fill:#dae8fc,stroke:#6c8ebf
    style DONE fill:#d5e8d4,stroke:#82b366
    style DROP1 fill:#f8cecc,stroke:#b85450
    style DROP2 fill:#f8cecc,stroke:#b85450
    style DROP3 fill:#f8cecc,stroke:#b85450
    style DROP4 fill:#f8cecc,stroke:#b85450
    style HQ fill:#fff2cc,stroke:#d6b656,stroke-dasharray: 5 5
```

---

## Fig 3 · 合成数据生成工作流

> 两条并行支路（拟真 vs 无意义），共用"LLM 生成 → 渲染 → Description"的骨架。重点体现：拟真用主题提示词驱动；无意义分 chaos / misleading 两种不同的提示策略；哈希去重防止雷同。

```mermaid
flowchart TD
    START["生成 500 条合成数据"]

    START --> M["拟真合成支路\n200 条"]
    START --> N["无意义合成支路\n300 条"]

    M --> MTHEME["主题提示词库\n90 个领域场景\n(微服务·CI/CD·数仓·IoT…)\n按编号轮流取模"]
    MTHEME --> MGEN["🤖 LLM 生成 Mermaid\n指定行数分布\n= 真实数据行数分布"]

    N --> N1["Chaos 支路\n150 条\n随机节点·无逻辑·荒谬组合"]
    N --> N2["Misleading 支路\n150 条\n有意义概念·但关系/顺序\n故意出错 4-6 处\n附「引入的反事实错误」清单"]
    N1 --> NGEN1["🤖 LLM 生成 Mermaid\n(混乱风格提示)"]
    N2 --> NGEN2["🤖 LLM 生成 Mermaid\n(误导风格提示)"]

    MGEN --> DEDUP{"哈希去重"}
    NGEN1 --> DEDUP
    NGEN2 --> DEDUP

    DEDUP -- 重复 --> RETRY["重新生成"]
    RETRY --> DEDUP

    DEDUP -- 通过 --> RENDER2["mermaid.ink\n渲染 PNG"]
    RENDER2 -- 失败 --> RETRY
    RENDER2 -- 成功 --> DESC2["生成 Description\n🤖 LLM 纯基于 Mermaid\n无外部仓库上下文"]
    DESC2 --> SMETA["写入 synthetic_metadata.json\n标注 source / nonsense_subtype\nmisleading 额外记录错误清单"]

    HQ2(["👤 人工抽检\n验证子类型定义是否符合预期"])
    SMETA -. 支持 .-> HQ2

    SMETA --> SDONE["✅ 入库\n500 条合成样本"]

    style START fill:#fff2cc,stroke:#d6b656
    style SDONE fill:#d5e8d4,stroke:#82b366
    style HQ2 fill:#fff2cc,stroke:#d6b656,stroke-dasharray: 5 5
    style N2 fill:#f8cecc,stroke:#b85450
    style N1 fill:#f8cecc,stroke:#b85450
```

---

## Fig 4 · Description 生成工作流

> 真实图和合成图在 Description 生成上有不同的上下文来源。这张图专门拆开这两条路径，展示 LLM 如何综合多源信息生成 7 节结构化描述，以及描述在后续 QA 生成中的作用。

```mermaid
flowchart LR
    subgraph INPUT ["输入来源"]
        MMD["diagram.mmd\nMermaid 源码"]
        PNG["diagram.png\n渲染图片"]
    end

    subgraph CTX_REAL ["真实数据额外上下文"]
        direction TB
        README["仓库 README"]
        SRCFILE["图所在文档片段"]
        RELFILE["AI 挑选的相关代码文件\n(≤6 个)"]
    end

    subgraph CTX_SYN ["合成数据上下文"]
        direction TB
        NOEXT["无外部上下文\n（仅 Mermaid 本身）"]
    end

    MMD --> LLM
    PNG --> LLM
    README --> LLM
    SRCFILE --> LLM
    RELFILE --> LLM
    NOEXT --> LLM

    LLM["🤖 多模态 LLM\n(Gemini 2.0 Flash)"]

    LLM --> DESC_OUT["description.txt\n7 节结构化描述\n① 图类型与用途\n② 整体布局\n③ 分组/阶段说明\n④ 节点逐项说明\n⑤ 连线与分支关系\n⑥ 仓库语境与术语\n⑦ QA Ground Truth 摘要"]

    DESC_OUT --> QA_USE["后续 QA 生成\n作为出题依据\n(前 7500 字)"]

    HQ3(["👤 人工抽查\n确保描述忠实于图\n无编造信息"])
    DESC_OUT -. 支持 .-> HQ3

    style LLM fill:#e1d5e7,stroke:#9673a6
    style DESC_OUT fill:#dae8fc,stroke:#6c8ebf
    style QA_USE fill:#d5e8d4,stroke:#82b366
    style HQ3 fill:#fff2cc,stroke:#d6b656,stroke-dasharray: 5 5
```

---

## Fig 5 · QA 生成工作流

> 强调"能拉开模型差距"是题目设计的核心目标；展示四种题目设计策略的并列关系；以及题目类型 / 难度标注的分布约束。

```mermaid
flowchart TD
    IN["每条样本\ndiagram.mmd + description.txt"]

    IN --> PROMPT["🤖 LLM 出题提示词\n目标: 让 8B / 30B / 235B\n及 instruct / thinking\n在准确率上拉开差距"]

    PROMPT --> STRAT["题目设计策略（四选其一或组合）"]

    STRAT --> S1["多跳推理\n从 X 到 Y 必经哪一节点\n若分支选 No 最终到达哪"]
    STRAT --> S2["易混选项\n两个选项均在图中出现\n需仔细读图才能区分"]
    STRAT --> S3["长链 / 远距离\n起点到终点的完整节点序列\n非直接相邻的远端节点"]
    STRAT --> S4["否定题\n「以下哪个不是」\n干扰项为图中或领域常见词"]

    S1 --> CONSTRAINT["分布约束\n共 6 题 / 样本\n≥2 reasoning · ≥1 negation\nhard ≥2 · easy ≤1"]
    S2 --> CONSTRAINT
    S3 --> CONSTRAINT
    S4 --> CONSTRAINT

    CONSTRAINT --> RAW["LLM 原始输出\nJSON 数组"]
    RAW --> PARSE{"解析 & 校验\n选项完整?\n correct_index 合法?\n type/difficulty 合法?"}
    PARSE -- 解析失败/不合格 --> RETRY2["重试 (最多3次)"]
    RETRY2 --> RAW

    PARSE -- 通过 --> QA_OUT["qa.json\n每题: question · options\ncorrect_index · type · difficulty"]

    HQ4(["👤 人工核查\n抽查答案唯一性\n与图的对应关系"])
    QA_OUT -. 支持 .-> HQ4

    style PROMPT fill:#e1d5e7,stroke:#9673a6
    style CONSTRAINT fill:#fff2cc,stroke:#d6b656
    style QA_OUT fill:#d5e8d4,stroke:#82b366
    style HQ4 fill:#fff2cc,stroke:#d6b656,stroke-dasharray: 5 5
    style S1 fill:#dae8fc,stroke:#6c8ebf
    style S2 fill:#dae8fc,stroke:#6c8ebf
    style S3 fill:#dae8fc,stroke:#6c8ebf
    style S4 fill:#dae8fc,stroke:#6c8ebf
```

---

## Fig 6 · QA 题型与难度分类体系

> 这张图适合放在"评测设计"小节前，用来解释 factual / reasoning / negation 三类题型的认知操作差异，以及 easy / medium / hard 的区分标准。矩阵式布局比纯文字表格更直观。

```mermaid
graph LR
    subgraph TYPE ["题目类型 — 认知操作轴"]
        F["Factual（事实）\n单步提取\n答案在图中直接可见\n测: 是否真的看图"]
        R["Reasoning（推理）\n多步推理\n整合多节点/路径关系\n测: 结构理解与推理链"]
        N["Negation（否定）\n排除判断\n理解「不是」并抑制常识\n测: 完整理解+抵抗干扰"]
    end

    subgraph DIFF ["题目难度 — 所需步数轴"]
        E["Easy\n单步·答案明显可见\n大多数模型能答对\n保证基线"]
        M["Medium\n看图+简单推理\n顺序·相邻节点关系\n区分\"表面\"与\"会推一步\""]
        H["Hard\n多步/长链/易混/否定\n非相邻节点·两个选项都在图中\n拉开参数量与模型形态差距"]
    end

    F --- E
    F --- M
    R --- M
    R --- H
    N --- M
    N --- H

    style F fill:#dae8fc,stroke:#6c8ebf
    style R fill:#dae8fc,stroke:#6c8ebf
    style N fill:#dae8fc,stroke:#6c8ebf
    style E fill:#d5e8d4,stroke:#82b366
    style M fill:#fff2cc,stroke:#d6b656
    style H fill:#f8cecc,stroke:#b85450
```

---

## Fig 7 · 搜索关键词与合成主题词全景（词云替代方案）

> Mermaid 本身不支持词云。这里用两个并列的 mindmap（思维导图）替代：一个展示爬取真实数据用到的主要关键词分类；一个展示 LLM 生成拟真数据用到的主题词分类。如需真正的词云，用 Python wordcloud 库另行生成。

### 7A · GitHub 搜索关键词（真实数据）

```mermaid
mindmap
  root((GitHub 搜索\n关键词))
    图类型关键词
      graph TD / LR / TB
      flowchart TD / LR
    架构领域
      microservices
      system design
      API gateway
      distributed system
      kubernetes / docker
      cloud / infrastructure
    流程领域
      CI/CD
      pipeline
      workflow
      deployment
      onboarding / approval
    组件关键词
      database / caching
      message queue
      load balancer
      authentication
      monitoring / logging
    数据领域
      data flow
      real-time
      batch
      migration
      sync
```

### 7B · LLM 生成拟真合成数据主题词

```mermaid
mindmap
  root((合成数据\n主题提示词))
    交易 & 支付
      订单创建与支付
      支付回调与对账
      对账与结算
      发票申请与开具
    用户 & 权限
      用户注册与登录
      权限与角色校验
      会话与单点登录
      多租户隔离
    系统架构
      API 网关路由与鉴权
      微服务间 RPC 调用
      服务发现与健康检查
      容器编排与扩缩容
      重试与熔断
    数据 & 存储
      缓存读写与失效
      数据库读写分离
      分库分表路由
      事件溯源
      数据湖分层
    运营 & 运维
      配置中心下发
      灰度发布与流量切换
      链路追踪
      备份与恢复
      密钥轮换
    推荐 & AI
      推荐排序 pipeline
      特征工程 pipeline
      模型训练与部署
      AB 实验分流
    物流 & 电商
      仓储入库与出库
      物流轨迹与签收
      退换货流程
      优惠券发放与核销
```

---

## 附注

- **人工审查** 在所有流程图中以**虚线框**标注，代表"支持性质检"而非强制节点，实际执行为抽样核查。
- **词云（Fig 7）** 的 Mermaid mindmap 版本适合论文/报告渲染；如需投稿到图片要求严格的期刊，建议用 Python `wordcloud` 库另外生成真实词云图，两者可互补。
- 所有流程图均已在 [mermaid.live](https://mermaid.live) 验证可渲染。
