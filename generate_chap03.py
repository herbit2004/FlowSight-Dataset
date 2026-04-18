#!/usr/bin/env python3
"""
第三章流程图生成 - 使用 Mermaid 渲染 PNG
使用 mermaid.ink API 渲染，与数据集生成流程一致
"""

import os
import base64
import urllib.request
import urllib.error
import json
import time
import requests

BASE_PATH = '/Users/herbit/Desktop/code/FlowSight-Dataset/paper/sysu_thesis/sysu-thesis-1.1.20230212/image/chap03'
os.makedirs(BASE_PATH, exist_ok=True)

def render_mermaid(mermaid_code: str, output_path: str, width: int = 1200, retries: int = 3) -> bool:
    """使用 mermaid.ink 渲染 Mermaid 代码为 PNG"""
    for attempt in range(retries):
        try:
            # 编码 Mermaid 代码
            encoded = base64.urlsafe_b64encode(mermaid_code.encode('utf-8')).decode('utf-8')
            url = f"https://mermaid.ink/img/{encoded}?type=png&width={width}"
            
            # 使用 requests 下载
            r = requests.get(url, timeout=45)
            if r.status_code != 200:
                print(f"  -> Attempt {attempt+1}: HTTP {r.status_code}")
                time.sleep(2)
                continue
            
            img_data = r.content
            
            # 检查是否返回了错误页面
            if len(img_data) < 1000:
                print(f"  -> Attempt {attempt+1} failed: Response too small ({len(img_data)} bytes)")
                time.sleep(2)
                continue
            
            # 保存图片
            with open(output_path, 'wb') as f:
                f.write(img_data)
            print(f"  -> Saved: {output_path}")
            return True
        except Exception as e:
            print(f"  -> Attempt {attempt+1} failed: {e}")
            time.sleep(2)
    print(f"  -> Error rendering {output_path}: All attempts failed")
    return False

# ============ Mermaid 图表定义 ============

# Fig 1: 数据集整体结构（简化版本）
FIG1_DATASET_STRUCTURE = '''graph TD
    DS[("FlowSight 数据集<br/>共 1000 条样本")]
    DS --> REAL["Real<br/>500 条<br/>来自 GitHub"]
    DS --> SYN["合成数据<br/>500 条<br/>LLM 生成"]
    SYN --> MEAN["Meaningful<br/>200 条"]
    SYN --> NONE["无意义<br/>300 条"]
    NONE --> CHAOS["Chaos<br/>150 条"]
    NONE --> MISLED["Misleading<br/>150 条"]
    REAL --> ITEM["样本格式<br/>mmd + png + txt + json"]
    MEAN --> ITEM
    CHAOS --> ITEM
    MISLED --> ITEM
    ITEM --> QA["每样本 6 道题<br/>F/R/N × E/M/H"]
    style DS fill:#f0f4ff,stroke:#6c8ebf,stroke-width:2px
    style REAL fill:#d5e8d4,stroke:#82b366
    style SYN fill:#fff2cc,stroke:#d6b656
    style MEAN fill:#ffe6cc,stroke:#d79b00
    style NONE fill:#f8cecc,stroke:#b85450
    style CHAOS fill:#f8cecc,stroke:#b85450
    style MISLED fill:#f8cecc,stroke:#b85450
    style ITEM fill:#dae8fc,stroke:#6c8ebf
    style QA fill:#e1d5e7,stroke:#9673a6'''

# Fig 2: 真实数据采集与标注工作流
FIG2_REAL_DATA = '''flowchart TD
    Q["🔍 GitHub 搜索
    40+ 组关键词
    (mermaid + 领域词)"]

    Q --> R["按 Star 数排序
    候选仓库列表"]

    R --> DOC["抓取 README / 文档
    提取 Mermaid 代码块"]

    DOC --> RULE{"规则过滤
    行数 ≥ 6
    连线数 ≥ 3
    标签有意义?"}
    RULE -- 不通过 --> DROP1["❌ 丢弃"]
    RULE -- 通过 --> HASH{"结构哈希去重
    (节点边集合)"}

    HASH -- 重复 --> DROP2["❌ 去重丢弃"]
    HASH -- 新样本 --> AI{"🤖 AI 质检
    Gemini 判断
    是否真实业务图?"}
    AI -- 否 --> DROP3["❌ 丢弃"]
    AI -- 是 --> RENDER["mermaid.ink
    渲染 PNG"]
    RENDER -- 失败 --> DROP4["❌ 渲染失败丢弃"]
    RENDER -- 成功 --> DESC["生成 Description
    多模态 LLM
    结合 README / 仓库上下文"]
    DESC --> META["写入 metadata.json
    记录来源仓库 · 星数 · 行数"]

    HQ(["👤 人工抽检
    验证质量与多样性"])
    AI -. 支持 .-> HQ
    DESC -. 支持 .-> HQ

    META --> DONE["✅ 入库
    500 条真实样本"]

    style Q fill:#dae8fc,stroke:#6c8ebf
    style DONE fill:#d5e8d4,stroke:#82b366
    style DROP1 fill:#f8cecc,stroke:#b85450
    style DROP2 fill:#f8cecc,stroke:#b85450
    style DROP3 fill:#f8cecc,stroke:#b85450
    style DROP4 fill:#f8cecc,stroke:#b85450
    style HQ fill:#fff2cc,stroke:#d6b656,stroke-dasharray: 5 5'''

# Fig 3: 合成数据生成工作流
FIG3_SYNTHETIC_DATA = '''flowchart TD
    START["生成 500 条合成数据"]

    START --> M["拟真合成支路
    200 条"]
    START --> N["无意义合成支路
    300 条"]

    M --> MTHEME["主题提示词库
    90 个领域场景
    (微服务·CI/CD·数仓·IoT…)
    按编号轮流取模"]
    MTHEME --> MGEN["🤖 LLM 生成 Mermaid
    指定行数分布
    = 真实数据行数分布"]

    N --> N1["Chaos 支路
    150 条
    随机节点·无逻辑·荒谬组合"]
    N --> N2["Misleading 支路
    150 条
    有意义概念·但关系/顺序
    故意出错 4-6 处
    附「引入的反事实错误」清单"]
    N1 --> NGEN1["🤖 LLM 生成 Mermaid
    (混乱风格提示)"]
    N2 --> NGEN2["🤖 LLM 生成 Mermaid
    (误导风格提示)"]

    MGEN --> DEDUP{"哈希去重"}
    NGEN1 --> DEDUP
    NGEN2 --> DEDUP

    DEDUP -- 重复 --> RETRY["重新生成"]
    RETRY --> DEDUP

    DEDUP -- 通过 --> RENDER2["mermaid.ink
    渲染 PNG"]
    RENDER2 -- 失败 --> RETRY
    RENDER2 -- 成功 --> DESC2["生成 Description
    🤖 LLM 纯基于 Mermaid
    无外部仓库上下文"]
    DESC2 --> SMETA["写入 synthetic_metadata.json
    标注 source / nonsense_subtype
    额外记录错误清单"]

    HQ2(["👤 人工抽检
    验证子类型定义是否符合预期"])
    SMETA -. 支持 .-> HQ2

    SMETA --> SDONE["✅ 入库
    500 条合成样本"]

    style START fill:#fff2cc,stroke:#d6b656
    style SDONE fill:#d5e8d4,stroke:#82b366
    style HQ2 fill:#fff2cc,stroke:#d6b656,stroke-dasharray: 5 5
    style N2 fill:#f8cecc,stroke:#b85450
    style N1 fill:#f8cecc,stroke:#b85450'''

# Fig 4: Description 生成工作流
FIG4_DESCRIPTION = '''flowchart LR
    subgraph INPUT ["输入来源"]
        MMD["diagram.mmd
        Mermaid 源码"]
        PNG["diagram.png
        渲染图片"]
    end

    subgraph CTX_REAL ["真实数据额外上下文"]
        direction TB
        README["仓库 README"]
        SRCFILE["图所在文档片段"]
        RELFILE["AI 挑选的相关代码文件
        (≤6 个)"]
    end

    subgraph CTX_SYN ["合成数据上下文"]
        direction TB
        NOEXT["无外部上下文
        （仅 Mermaid 本身）"]
    end

    MMD --> LLM
    PNG --> LLM
    README --> LLM
    SRCFILE --> LLM
    RELFILE --> LLM
    NOEXT --> LLM

    LLM["🤖 多模态 LLM
    (Gemini 2.0 Flash)"]

    LLM --> DESC_OUT["description.txt
    7 节结构化描述
    ① 图类型与用途
    ② 整体布局
    ③ 分组/阶段说明
    ④ 节点逐项说明
    ⑤ 连线与分支关系
    ⑥ 仓库语境与术语
    ⑦ QA Ground Truth 摘要"]

    DESC_OUT --> QA_USE["后续 QA 生成
    作为出题依据
    (前 7500 字)"]

    HQ3(["👤 人工抽查
    确保描述忠实于图
    无编造信息"])
    DESC_OUT -. 支持 .-> HQ3

    style LLM fill:#e1d5e7,stroke:#9673a6
    style DESC_OUT fill:#dae8fc,stroke:#6c8ebf
    style QA_USE fill:#d5e8d4,stroke:#82b366
    style HQ3 fill:#fff2cc,stroke:#d6b656,stroke-dasharray: 5 5'''

# Fig 5: QA 生成工作流（题目设计策略合并为一个节点）
FIG5_QA_GENERATION = '''flowchart TD
    IN["每条样本
    diagram.mmd + description.txt"]

    IN --> PROMPT["LLM 出题提示词
    目标: 让 8B/30B/235B
    及 instruct/thinking
    在准确率上拉开差距"]

    PROMPT --> STRAT["题目设计策略
    (整合多跳推理、易混选项、
    长链/远距离、否定题)"]

    STRAT --> CONSTRAINT["分布约束
    6题/样本
    >=2 reasoning
    >=1 negation
    hard>=2
    easy<=1"]

    CONSTRAINT --> RAW["LLM原始输出
    JSON数组"]
    RAW --> PARSE{"解析&校验
    选项完整?
    correct_index合法?
    type/difficulty合法?"}
    PARSE -- 解析失败 --> RETRY2["重试(最多3次)"]
    RETRY2 --> RAW
    PARSE -- 通过 --> QA_OUT["qa.json
    question/options
    correct_index
    type/difficulty"]

    HQ4(["人工核查
    抽查答案唯一性"])
    QA_OUT -. 支持 .-> HQ4

    style PROMPT fill:#e1d5e7,stroke:#9673a6
    style STRAT fill:#dae8fc,stroke:#6c8ebf
    style CONSTRAINT fill:#fff2cc,stroke:#d6b656
    style QA_OUT fill:#d5e8d4,stroke:#82b366
    style HQ4 fill:#fff2cc,stroke:#d6b656,stroke-dasharray:5 5'''

# Fig 7: 迭代优化流程
FIG7_PILOT_ITERATION = '''flowchart TD
    subgraph ITER["迭代开发"]
        A["真实样本分析"] --> B["题型设计"]
        B --> C["Prompt调优"]
        C --> D["小规模验证"]
        D --> E["四类数据扩展"]
    end
    
    subgraph NORM["规范化"]
        E --> F["全量QA规范"]
        F --> G["批量生成"]
    end
    
    style A fill:#3498db,color:#fff
    style B fill:#9b59b6,color:#fff
    style C fill:#e74c3c,color:#fff
    style D fill:#e67e22,color:#fff
    style E fill:#27ae60,color:#fff
    style F fill:#f39c12,color:#fff
    style G fill:#2c3e50,color:#fff'''

# Fig 6A: GitHub 搜索关键词（放射状思维导图）
FIG6A_KEYWORDS = '''mindmap
  root((GitHub<br/>搜索<br/>关键词))
    图类型[图类型]
      graph[graph TD/LR/TB]
      flowchart[flowchart TD/LR]
    架构领域[架构领域]
      microservices[microservices]
      system_design[system design]
      api_gateway[API gateway]
      distributed[k8s/docker]
    流程领域[流程领域]
      cicd[CI/CD]
      pipeline[pipeline]
      workflow[workflow]
    组件关键词[组件关键词]
      database[database/caching]
      mq[message queue]
      lb[load balancer]
    数据领域[数据领域]
      data_flow[data flow]
      realtime[real-time]
      batch[batch]'''

# Fig 7B: LLM 生成主题词（放射状思维导图）
FIG7B_THEMES = '''mindmap
  root((合成数据<br/>主题<br/>提示词))
    交易支付[交易&支付]
      order[订单创建与支付]
      callback[支付回调与对账]
      settle[对账与结算]
    用户权限[用户&权限]
      register[用户注册与登录]
      auth[权限与角色校验]
      sso[会话与单点登录]
    系统架构[系统架构]
      gateway[API网关路由与鉴权]
      rpc[微服务间RPC调用]
      health[服务发现与健康检查]
    数据存储[数据&存储]
      cache[缓存读写与失效]
      db[数据库读写分离]
      shard[分库分表路由]
    运营运维[运营&运维]
      config[配置中心下发]
      deploy[灰度发布与流量切换]
    推荐AI[推荐&AI]
      rec[推荐排序pipeline]
      ml[模型训练与部署]
    物流电商[物流&电商]
      warehouse[仓储入库与出库]
      logistics[物流轨迹与签收]'''

# ============ 主程序 ============

print("=" * 60)
print("开始生成第三章 Mermaid 流程图...")
print("=" * 60)

# Fig 1: 数据集结构
print("\n[1/8] 生成 Fig 1: 数据集整体结构...")
render_mermaid(FIG1_DATASET_STRUCTURE, f"{BASE_PATH}/dataset_structure.png")

# Fig 2: 真实数据流程
print("\n[2/8] 生成 Fig 2: 真实数据采集与标注工作流...")
render_mermaid(FIG2_REAL_DATA, f"{BASE_PATH}/real_data_pipeline.png", width=1600)

# Fig 3: 合成数据生成流程
print("\n[3/8] 生成 Fig 3: 合成数据生成工作流...")
render_mermaid(FIG3_SYNTHETIC_DATA, f"{BASE_PATH}/synthetic_data_pipeline.png", width=1600)

# Fig 4: Description 生成流程
print("\n[4/7] 生成 Fig 4: Description 生成工作流...")
render_mermaid(FIG4_DESCRIPTION, f"{BASE_PATH}/description_pipeline.png", width=1400)

# Fig 5: QA 生成流程
print("\n[5/7] 生成 Fig 5: QA 生成工作流...")
render_mermaid(FIG5_QA_GENERATION, f"{BASE_PATH}/qa_pipeline.png", width=1400)

# Fig 6: 迭代优化流程
print("\n[6/7] 生成 Fig 6: 迭代优化流程...")
render_mermaid(FIG7_PILOT_ITERATION, f"{BASE_PATH}/pilot_iteration.png", width=1200)

# Fig 7: GitHub 搜索关键词
print("\n[7/7] 生成 Fig 7: GitHub 搜索关键词...")
render_mermaid(FIG6A_KEYWORDS, f"{BASE_PATH}/keywords_github.png", width=1200)

# Fig 8: LLM 生成主题词
print("\n[8/7] 生成 Fig 8: LLM 生成主题词...")
render_mermaid(FIG7B_THEMES, f"{BASE_PATH}/themes_synthetic.png", width=1200)

print("\n" + "=" * 60)
print("第三章 Mermaid 流程图生成完成！")
print("=" * 60)
