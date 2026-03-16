#!/usr/bin/env python3
"""
第四章流程图生成 - 使用 Mermaid 渲染 PNG
使用 mermaid.ink API 渲染
"""

import os
import base64
import urllib.request
import urllib.error

BASE_PATH = '/Users/herbit/Desktop/code/FlowSight-Dataset/paper/sysu_thesis/sysu-thesis-1.1.20230212/image/chap04'
os.makedirs(BASE_PATH, exist_ok=True)

def render_mermaid(mermaid_code: str, output_path: str, width: int = 1200) -> bool:
    """使用 mermaid.ink 渲染 Mermaid 代码为 PNG"""
    try:
        # 编码 Mermaid 代码
        encoded = base64.urlsafe_b64encode(mermaid_code.encode('utf-8')).decode('utf-8')
        url = f"https://mermaid.ink/img/{encoded}?type=png&width={width}"
        
        # 下载图片
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            img_data = response.read()
        
        # 保存图片
        with open(output_path, 'wb') as f:
            f.write(img_data)
        print(f"  -> Saved: {output_path}")
        return True
    except Exception as e:
        print(f"  -> Error rendering {output_path}: {e}")
        return False

# ============ Mermaid 图表定义 ============

# Fig 1: 任务输入输出
FIG1_TASK_IO = '''flowchart TB
    subgraph INPUT ["输入"]
        IMG["流程图图片
        diagram.png"]
        QLIST["6道选择题
        question + options"]
    end
    
    subgraph MODEL ["多模态大模型"]
        VIS["视觉编码器
        Vision Encoder"]
        LLM["大语言模型
        LLM"]
        VIS --> LLM
    end
    
    subgraph OUTPUT ["输出"]
        ANS["答案序列
        ABDCBD"]
    end
    
    IMG --> VIS
    QLIST --> LLM
    LLM --> ANS
    
    style INPUT fill:#e3f2fd,stroke:#1565c0
    style MODEL fill:#e8f5e9,stroke:#2e7d32
    style OUTPUT fill:#fce4ec,stroke:#c62828'''

# Fig 2: Benchmark 执行流程
FIG2_BENCHMARK = '''flowchart TD
    START["分层抽样
    500条样本"]
    
    START --> PREP["构造评测任务
    图片 + 题目"]
    
    PREP --> INVOKE["模型调用
    OpenRouter API
    批量请求"]
    
    INVOKE --> CHECK{"成功?"}
    CHECK -- 否 --> RETRY["重试
    最多3次"]
    RETRY --> INVOKE
    CHECK -- 是 --> VALID["结果校验
    解析JSON
    验证答案"]
    
    VALID --> LOG["详细日志
    输入/输出/耗时
    token消耗"]
    
    LOG --> AGG["聚合统计
    准确率/分模型
    分题型/分数据类型"]
    
    AGG --> REPORT["生成报告
    图表/表格
    结论摘要"]
    
    style START fill:#2196f3,stroke:#fff
    style INVOKE fill:#ff9800,stroke:#000
    style CHECK fill:#9c27b0,stroke:#fff
    style RETRY fill:#f44336,stroke:#fff
    style VALID fill:#4caf50,stroke:#fff
    style LOG fill:#00bcd4,stroke:#fff
    style AGG fill:#3f51b5,stroke:#fff
    style REPORT fill:#795548,stroke:#fff'''

# Fig 3: 评测指标体系（新增）
FIG3_METRICS = '''graph LR
    subgraph ACCURACY ["准确率指标"]
        AC["整体准确率"]
        AC_BY_DTYPE["按数据类型
        Real/Meaningful
        Chaos/Misleading"]
        AC_BY_QTYPE["按题型
        Factual/Reasoning
        Negation"]
        AC_BY_DIFF["按难度
        Easy/Medium/Hard"]
    end
    
    subgraph ANALYSIS ["分析维度"]
        MODEL_COMP["模型对比
        开源vs闭源
        参数规模效应"]
        THINK["Thinking模式
        vs Instruct模式
        思考长度分析"]
        CROSS["交叉分析
        数据×题型
        模型×数据"]
    end
    
    AC --> AC_BY_DTYPE
    AC --> AC_BY_QTYPE
    AC --> AC_BY_DIFF
    AC --> MODEL_COMP
    MODEL_COMP --> THINK
    THINK --> CROSS
    
    style ACCURACY fill:#e3f2fd,stroke:#1565c0
    style ANALYSIS fill:#fff3e0,stroke:#e65100'''

# ============ 主程序 ============

print("=" * 60)
print("开始生成第四章 Mermaid 流程图...")
print("=" * 60)

# Fig 1: 任务输入输出
print("\n[1/3] 生成 Fig 1: 任务输入输出...")
render_mermaid(FIG1_TASK_IO, f"{BASE_PATH}/task_io.png", width=1200)

# Fig 2: Benchmark 执行流程
print("\n[2/3] 生成 Fig 2: Benchmark 执行流程...")
render_mermaid(FIG2_BENCHMARK, f"{BASE_PATH}/benchmark_pipeline.png", width=1200)

# Fig 3: 评测指标体系
print("\n[3/3] 生成 Fig 3: 评测指标体系...")
render_mermaid(FIG3_METRICS, f"{BASE_PATH}/evaluation_metrics.png", width=1200)

print("\n" + "=" * 60)
print("第四章 Mermaid 流程图生成完成！")
print("=" * 60)
