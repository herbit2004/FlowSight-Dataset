#!/usr/bin/env python3
"""
第四章流程图生成 - 使用Matplotlib
"""

import os

BASE_PATH = '/Users/herbit/Desktop/code/FlowSight-Dataset/paper/sysu_thesis/sysu-thesis-1.1.20230212/image/chap04'
os.makedirs(BASE_PATH, exist_ok=True)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

def create_flowchart(name, boxes, arrows, title=""):
    """创建流程图"""
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    if title:
        ax.set_title(title, fontsize=16, fontweight='bold', pad=15)
    
    # 绘制所有节点
    for box in boxes:
        if len(box) == 6:
            x, y, w, h, text, bg = box
            fg = '#fff'
        else:
            x, y, w, h, text, bg, fg = box
            
        rect = FancyBboxPatch((x, y), w, h,
                              boxstyle="round,pad=0.05",
                              facecolor=bg, edgecolor='#333', linewidth=2)
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

print("开始生成第四章流程图...")

# 图1: 任务输入输出
boxes = [
    # 输入框
    (1, 6.5, 2.5, 1.2, 'Flowchart\nImage (PNG)', '#E3F2FD', '#1565C0'),
    (1, 4.5, 2.5, 1.2, 'Question\nList (6 MCQ)', '#E3F2FD', '#1565C0'),
    # 模型处理框
    (5, 6.5, 2.5, 1.2, 'Visual\nUnderstanding', '#E8F5E9', '#2E7D32'),
    (5, 4.5, 2.5, 1.2, 'Text\nUnderstanding', '#E8F5E9', '#2E7D32'),
    (8.5, 5.5, 2.5, 1.2, 'Reasoning\n& Decision', '#FFF3E0', '#E65100'),
    # 输出框
    (12, 5.5, 2, 1.2, 'Answers\n(ABACBD)', '#FCE4EC', '#C62828'),
]
arrows = [
    ((3.5, 7), (5, 7), '->', '#333'),
    ((3.5, 5.2), (5, 5.2), '->', '#333'),
    ((7.5, 7), (9.2, 6.2), '->', '#333'),
    ((7.5, 4.5), (9.2, 5.5), '->', '#333'),
    ((11, 6), (12, 6), '->', '#333'),
]
create_flowchart('task_io', boxes, arrows, 'Task Input and Output')

# 图2: Benchmark执行流程
boxes = [
    (0.5, 8, 2.5, 1.2, 'Stratified\nSampling\n(500 samples)', '#2196F3', '#fff'),
    (4, 8, 2.5, 1.2, 'Task\nConstruction\n(Image+Question)', '#4CAF50', '#fff'),
    (7.5, 8, 2.5, 1.2, 'Model\nInvocation\n(API Batch)', '#FF9800', '#000'),
    (11, 8, 2.5, 1.2, 'Success?', '#9C27B0', '#fff'),
    (11, 5.5, 2.5, 1.2, 'Retry\n(Max 3)', '#F44336', '#fff'),
    (4, 5.5, 2.5, 1.2, 'Result\nValidation', '#4CAF50', '#fff'),
    (4, 3, 2.5, 1.2, 'Logging\n(Details)', '#00BCD4', '#fff'),
    (7.5, 3, 2.5, 1.2, 'Report\nGeneration', '#3F51B5', '#fff'),
]
arrows = [
    ((3, 8.5), (4, 8.5), '->', '#333'),
    ((6.5, 8.5), (7.5, 8.5), '->', '#333'),
    ((9.75, 8), (10, 7.2), '->', '#333'),
    ((11, 8), (11, 6.5), '->', '#333'),
    ((12.5, 5.5), (12.5, 7), '->', '#333'),
    ((8, 8.5), (9, 8), '->', '#333'),  # success path
    ((11, 5.5), (9, 5.5), '->', '#333'),
    ((6.5, 5.5), (4, 5.5), '->', '#333'),
    ((4, 5.5), (4, 4), '->', '#333'),
    ((6.5, 3), (7.5, 3), '->', '#333'),
]
create_flowchart('benchmark_pipeline', boxes, arrows, 'Benchmark Execution Pipeline')

print("第四章流程图生成完成！")
