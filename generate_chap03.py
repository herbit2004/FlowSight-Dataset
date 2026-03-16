#!/usr/bin/env python3
"""
第三章流程图生成 - 使用Matplotlib
"""

import os

BASE_PATH = '/Users/herbit/Desktop/code/FlowSight-Dataset/paper/sysu_thesis/sysu-thesis-1.1.20230212/image/chap03'
os.makedirs(BASE_PATH, exist_ok=True)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patches as mpatches

def create_flowchart(name, boxes, arrows, title=""):
    """创建流程图"""
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    if title:
        ax.set_title(title, fontsize=16, fontweight='bold', pad=15)
    
    # 绘制所有节点
    for box in boxes:
        x, y, w, h, text, bg, fg = box
        rect = FancyBboxPatch((x, y), w, h,
                              boxstyle="round,pad=0.05",
                              facecolor=bg, edgecolor=fg, linewidth=2)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, text, ha='center', va='center',
               fontsize=11, color=fg, fontweight='bold')
    
    # 绘制所有箭头
    for arrow in arrows:
        if len(arrow) == 4:
            start, end, style, color = arrow
            ax.annotate('', xy=end, xytext=start,
                       arrowprops=dict(arrowstyle=style, color=color, lw=2))
        else:
            start, end = arrow
            ax.annotate('', xy=end, xytext=start,
                       arrowprops=dict(arrowstyle='->', color='#333', lw=2))
    
    plt.tight_layout()
    plt.savefig(f'{BASE_PATH}/{name}.pdf', dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()

print("开始生成第三章流程图...")

# 图1: 数据集结构
boxes = [
    (5, 8.5, 4, 1, 'FlowSight\n数据集', '#1976D2', '#fff'),
    (2, 6, 2.5, 1, 'Real\n500条', '#4CAF50', '#fff'),
    (9.5, 6, 2.5, 1, 'LLM合成\n500条', '#2196F3', '#fff'),
    (3, 4, 2, 0.8, 'Meaningful\n200条', '#4CAF50', '#fff'),
    (7, 4, 2, 0.8, 'Chaos\n150条', '#FF9800', '#000'),
    (11, 4, 2, 0.8, 'Misleading\n150条', '#F44336', '#fff'),
]
arrows = [
    ((7, 8), (4.5, 6.2)),
    ((7, 8), (9.5, 6.2)),
    ((3.25, 6), (4, 4.8)),
    ((7.5, 6), (8, 4.8)),
    ((11.5, 6), (12, 4.8)),
]
create_flowchart('dataset_structure', boxes, arrows, 'FlowSight Dataset Structure')

# 图2: 真实数据流程
boxes = [
    (1, 4, 2, 1, '开源项目', '#2196F3', '#fff'),
    (4, 4, 2, 1, '流程图\n识别', '#4CAF50', '#fff'),
    (7, 4, 2, 1, 'Mermaid\n转换', '#4CAF50', '#fff'),
    (10, 4, 2, 1, '人工\n审核', '#FF9800', '#000'),
    (13, 4, 2, 1, 'Real\n数据', '#1976D2', '#fff'),
]
arrows = [
    ((3, 4.5), (4, 4.5), '->', '#333'),
    ((6, 4.5), (7, 4.5), '->', '#333'),
    ((9, 4.5), (10, 4.5), '->', '#333'),
    ((12, 4.5), (13, 4.5), '->', '#333'),
]
create_flowchart('real_data_pipeline', boxes, arrows, 'Real Data Collection Pipeline')

# 图3: 描述生成流程
boxes = [
    (1, 7, 2, 1, 'Mermaid\n源码', '#2196F3', '#fff'),
    (4, 7, 2, 1, 'LLM描述\n生成', '#4CAF50', '#fff'),
    (7, 7, 2, 1, '结构化\n解析', '#4CAF50', '#fff'),
    (10, 7, 2, 1, '验证?', '#FF9800', '#000'),
    (10, 5, 2, 1, '人工\n修正', '#F44336', '#fff'),
    (13, 7, 2, 1, '描述\n输出', '#1976D2', '#fff'),
]
arrows = [
    ((3, 7.5), (4, 7.5), '->', '#333'),
    ((6, 7.5), (7, 7.5), '->', '#333'),
    ((9, 7.5), (10, 7.5), '->', '#333'),
    ((11, 7), (11, 6), '->', '#333'),
    ((10, 5), (7, 5), '->', '#333'),
    ((12, 7.5), (13, 7.5), '->', '#333'),
]
create_flowchart('description_pipeline_real', boxes, arrows, 'Description Generation Pipeline (Real)')

# 图4: 合成数据生成流程
boxes = [
    (1, 7, 2, 1, '种子\n提示词', '#2196F3', '#fff'),
    (4, 7, 2, 1, 'LLM生成\nMermaid', '#4CAF50', '#fff'),
    (7, 7, 2, 1, '类型\n判定', '#FF9800', '#000'),
    (4, 5, 2, 0.8, 'Meaningful', '#4CAF50', '#fff'),
    (7, 5, 2, 0.8, 'Chaos', '#FF9800', '#000'),
    (10, 5, 2, 0.8, 'Misleading', '#F44336', '#fff'),
    (7, 3, 2, 1, '合成\n数据', '#1976D2', '#fff'),
]
arrows = [
    ((3, 7.5), (4, 7.5), '->', '#333'),
    ((6, 7.5), (7, 7.5), '->', '#333'),
    ((8, 7), (5, 5.8), '->', '#333'),
    ((8, 7), (8, 5.8), '->', '#333'),
    ((8, 7), (11, 5.8), '->', '#333'),
    ((5, 5), (8, 4), '->', '#333'),
    ((8, 5), (8, 4), '->', '#333'),
    ((10, 5), (9, 4), '->', '#333'),
]
create_flowchart('description_pipeline_synthetic', boxes, arrows, 'Synthetic Data Generation Pipeline')

# 图5: QA生成流程
boxes = [
    (1, 4, 2, 1, '流程图', '#2196F3', '#fff'),
    (4, 4, 2, 1, '题目\n生成', '#4CAF50', '#fff'),
    (7, 4, 2, 1, '选项\n构造', '#4CAF50', '#fff'),
    (10, 4, 2, 1, '答案\n标注', '#FF9800', '#000'),
    (13, 4, 2, 1, 'QA\n数据集', '#1976D2', '#fff'),
]
arrows = [
    ((3, 4.5), (4, 4.5), '->', '#333'),
    ((6, 4.5), (7, 4.5), '->', '#333'),
    ((9, 4.5), (10, 4.5), '->', '#333'),
    ((12, 4.5), (13, 4.5), '->', '#333'),
]
create_flowchart('qa_pipeline', boxes, arrows, 'QA Generation Pipeline')

# 图6: 迭代优化流程
boxes = [
    (1, 7, 2, 1, '初始\n数据集', '#9E9E9E', '#fff'),
    (4, 7, 2, 1, 'Pilot\n测试', '#2196F3', '#fff'),
    (7, 7, 2, 1, '评估\n结果?', '#FF9800', '#000'),
    (7, 5, 2, 1, '问题\n分析', '#F44336', '#fff'),
    (4, 3, 2, 1, '数据\n优化', '#4CAF50', '#fff'),
    (10, 7, 2, 1, '最终\n数据集', '#1976D2', '#fff'),
]
arrows = [
    ((3, 7.5), (4, 7.5), '->', '#333'),
    ((6, 7.5), (7, 7.5), '->', '#333'),
    ((8, 7), (8, 6), '->', '#333'),
    ((7, 5), (6, 3.5), '->', '#333'),
    ((4, 3), (4, 6.5), '->', '#333'),
    ((9, 7.5), (10, 7.5), '->', '#333'),
]
create_flowchart('pilot_iteration', boxes, arrows, 'Iteration and Optimization')

print("第三章流程图生成完成！")
