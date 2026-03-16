#!/usr/bin/env python3
"""
第五章实验结果图表生成
数据源: /Users/herbit/Desktop/code/FlowSight-Dataset/benchmark_run/state.json
"""

import json
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import numpy as np
import pandas as pd
import seaborn as sns

plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

BENCHMARK_PATH = '/Users/herbit/Desktop/code/FlowSight-Dataset/benchmark_run'
BASE_PATH = '/Users/herbit/Desktop/code/FlowSight-Dataset/paper/sysu_thesis/sysu-thesis-1.1.20230212/image/chap05'

def load_data():
    with open(f'{BENCHMARK_PATH}/state.json', 'r') as f:
        return json.load(f)

def generate_chap05_charts():
    print("加载benchmark数据...")
    data = load_data()
    
    # 样本ID到数据类型映射
    sample_to_dtype = {sid: sinfo['data_type'] for sid, sinfo in data['samples'].items()}
    
    models = [
        'qwen/qwen3-vl-8b-instruct',
        'qwen/qwen3-vl-30b-a3b-instruct', 
        'qwen/qwen3-vl-235b-a22b-instruct',
        'qwen/qwen3-vl-8b-thinking',
        'qwen/qwen3-vl-30b-a3b-thinking',
        'qwen/qwen3-vl-235b-a22b-thinking',
        'google/gemini-2.5-flash',
        'google/gemini-2.5-flash-image',
        'google/gemini-2.5-flash-lite',
        'openai/gpt-4o-mini',
        'minimax/minimax-01'
    ]
    
    dtypes = ['real', 'meaningful', 'chaos', 'misleading']
    dtype_names = {'real': 'Real', 'meaningful': 'Meaningful', 'chaos': 'Chaos', 'misleading': 'Misleading'}
    qtypes = ['factual', 'reasoning', 'negation']
    
    # ===== 1. 数据分布饼图 =====
    dtype_counts = {dt: 0 for dt in dtypes}
    for sinfo in data['samples'].values():
        dt = sinfo.get('data_type')
        if dt in dtype_counts:
            dtype_counts[dt] += 1
    
    fig, ax = plt.subplots(figsize=(10, 7))
    colors_pie = ['#2196F3', '#4CAF50', '#FF9800', '#F44336']
    labels = ['Real', 'Meaningful', 'Chaos', 'Misleading']
    sizes = [dtype_counts['real'], dtype_counts['meaningful'], dtype_counts['chaos'], dtype_counts['misleading']]
    
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors_pie, 
                                       autopct='%1.1f%%', startangle=90)
    for text in texts:
        text.set_fontsize(14)
        text.set_fontweight('bold')
    for autotext in autotexts:
        autotext.set_fontsize(13)
        autotext.set_fontweight('bold')
    ax.set_title('Data Distribution', fontsize=18, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'{BASE_PATH}/data_distribution.pdf', dpi=200)
    plt.close()
    print("已生成: data_distribution.pdf")
    
    # ===== 2. 各模型整体准确率 =====
    model_acc = {}
    for model in models:
        correct = sum(t['correct'] for k, t in data['tasks'].items() if t['model'] == model and t['status'] == 'done')
        total = sum(t['total'] for k, t in data['tasks'].items() if t['model'] == model and t['status'] == 'done')
        model_acc[model] = correct / total * 100 if total > 0 else 0
    
    sorted_models = sorted(model_acc.items(), key=lambda x: x[1], reverse=True)
    model_labels = [m[0].split('/')[-1].replace('-', '\n') for m in sorted_models]
    accuracies = [m[1] for m in sorted_models]
    
    fig, ax = plt.subplots(figsize=(16, 10))
    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(model_labels)))
    bars = ax.barh(range(len(model_labels)), accuracies, color=colors, height=0.6)
    ax.set_yticks(range(len(model_labels)))
    ax.set_yticklabels(model_labels, fontsize=11, fontweight='bold')
    ax.set_xlabel('Accuracy (%)', fontsize=15, fontweight='bold')
    ax.set_title('Overall Accuracy by Model', fontsize=18, fontweight='bold')
    ax.set_xlim(55, 95)
    for i, v in enumerate(accuracies):
        ax.text(v + 2.0, i, f'{v:.1f}%', va='center', fontsize=12, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{BASE_PATH}/overall_accuracy.pdf', dpi=200)
    plt.close()
    print("已生成: overall_accuracy.pdf")
    
    # ===== 3. 数据类型准确率 =====
    dtype_correct = {dt: 0 for dt in dtypes}
    dtype_total = {dt: 0 for dt in dtypes}
    for task in data['tasks'].values():
        if task['status'] == 'done':
            dtype = sample_to_dtype.get(task['sample_id'])
            if dtype in dtype_correct:
                dtype_correct[dtype] += task['correct']
                dtype_total[dtype] += task['total']
    
    dtype_acc = [dtype_correct[d]/dtype_total[d]*100 if dtype_total[d] > 0 else 0 for d in dtypes]
    
    fig, ax = plt.subplots(figsize=(10, 7))
    colors = ['#2196F3', '#4CAF50', '#FF9800', '#F44336']
    bars = ax.bar(range(len(dtypes)), dtype_acc, color=colors, width=0.6, edgecolor='black', linewidth=1.5)
    ax.set_xticks(range(len(dtypes)))
    ax.set_xticklabels([dtype_names[d] for d in dtypes], fontsize=14, fontweight='bold')
    ax.set_ylabel('Accuracy (%)', fontsize=15, fontweight='bold')
    ax.set_title('Accuracy by Data Type', fontsize=18, fontweight='bold')
    ax.set_ylim(0, 100)
    for bar, acc in zip(bars, dtype_acc):
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1.5, 
                f'{acc:.1f}%', ha='center', fontsize=13, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{BASE_PATH}/difficulty_analysis.pdf', dpi=200)
    plt.close()
    print("已生成: difficulty_analysis.pdf")
    
    # ===== 4. 题型整体准确率（用于5.4节，只有3根柱）=====
    # 计算所有模型的平均题型准确率
    qtype_correct = {q: 0 for q in qtypes}
    qtype_total = {q: 0 for q in qtypes}
    for task in data['tasks'].values():
        if task['status'] == 'done':
            for pq in task.get('per_question', []):
                qt = pq.get('type', '').lower()
                if qt in qtype_correct:
                    qtype_correct[qt] += 1 if pq.get('is_correct', False) else 0
                    qtype_total[qt] += 1
    
    qtype_acc = [qtype_correct[q]/qtype_total[q]*100 if qtype_total[q] > 0 else 0 for q in qtypes]
    
    fig, ax = plt.subplots(figsize=(10, 7))
    colors = ['#4CAF50', '#2196F3', '#FF5722']
    bars = ax.bar(range(len(qtypes)), qtype_acc, color=colors, width=0.6, edgecolor='black', linewidth=1.5)
    ax.set_xticks(range(len(qtypes)))
    ax.set_xticklabels([q.capitalize() for q in qtypes], fontsize=14, fontweight='bold')
    ax.set_ylabel('Accuracy (%)', fontsize=15, fontweight='bold')
    ax.set_title('Accuracy by Question Type (Overall)', fontsize=18, fontweight='bold')
    ax.set_ylim(0, 100)
    for bar, acc in zip(bars, qtype_acc):
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1.5, 
                f'{acc:.1f}%', ha='center', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{BASE_PATH}/qtype_overall_accuracy.pdf', dpi=200)
    plt.close()
    print("已生成: qtype_overall_accuracy.pdf")
    
    # ===== 4b. 题型准确率（按模型分组柱状图，用于5.6.2节）=====
    model_qtype = {q: {m: [] for m in models} for q in qtypes}
    for task in data['tasks'].values():
        if task['status'] == 'done':
            model = task['model']
            for pq in task.get('per_question', []):
                qt = pq.get('type', '').lower()
                if qt in model_qtype:
                    model_qtype[qt][model].append(1 if pq.get('is_correct', False) else 0)
    
    factual_acc = [np.mean(model_qtype['factual'].get(m, [0])) * 100 for m in models]
    reasoning_acc = [np.mean(model_qtype['reasoning'].get(m, [0])) * 100 for m in models]
    negation_acc = [np.mean(model_qtype['negation'].get(m, [0])) * 100 for m in models]
    
    fig, ax = plt.subplots(figsize=(14, 8))
    x = np.arange(len(models))
    width = 0.25
    ax.bar(x - width, factual_acc, width, label='Factual', color='#4CAF50', alpha=0.85, edgecolor='black', linewidth=0.5)
    ax.bar(x, reasoning_acc, width, label='Reasoning', color='#2196F3', alpha=0.85, edgecolor='black', linewidth=0.5)
    ax.bar(x + width, negation_acc, width, label='Negation', color='#FF5722', alpha=0.85, edgecolor='black', linewidth=0.5)
    ax.set_xlabel('Model', fontsize=14, fontweight='bold')
    ax.set_ylabel('Accuracy (%)', fontsize=14, fontweight='bold')
    ax.set_title('Accuracy by Question Type', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([m.split('/')[-1].replace('-', '\n') for m in models], fontsize=9, fontweight='bold')
    ax.legend(loc='upper right', fontsize=12)
    ax.set_ylim(0, 110)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{BASE_PATH}/question_type_accuracy.pdf', dpi=200)
    plt.close()
    print("已生成: question_type_accuracy.pdf")
    
    # ===== 5. 题型×数据类型 =====
    dt_qtype_correct = {dt: {q: 0 for q in qtypes} for dt in dtypes}
    dt_qtype_total = {dt: {q: 0 for q in qtypes} for dt in dtypes}
    for task in data['tasks'].values():
        if task['status'] == 'done':
            dtype = sample_to_dtype.get(task['sample_id'])
            if not dtype or dtype not in dt_qtype_correct:
                continue
            for pq in task.get('per_question', []):
                qt = pq.get('type', '').lower()
                if qt in dt_qtype_correct[dtype]:
                    dt_qtype_correct[dtype][qt] += 1 if pq.get('is_correct', False) else 0
                    dt_qtype_total[dtype][qt] += 1
    
    factual_data = [dt_qtype_correct[dt]['factual']/dt_qtype_total[dt]['factual']*100 if dt_qtype_total[dt]['factual'] > 0 else 0 for dt in dtypes]
    reasoning_data = [dt_qtype_correct[dt]['reasoning']/dt_qtype_total[dt]['reasoning']*100 if dt_qtype_total[dt]['reasoning'] > 0 else 0 for dt in dtypes]
    negation_data = [dt_qtype_correct[dt]['negation']/dt_qtype_total[dt]['negation']*100 if dt_qtype_total[dt]['negation'] > 0 else 0 for dt in dtypes]
    
    fig, ax = plt.subplots(figsize=(12, 8))
    x = np.arange(len(dtypes))
    width = 0.25
    ax.bar(x - width, factual_data, width, label='Factual', color='#4CAF50', alpha=0.85, edgecolor='black', linewidth=1)
    ax.bar(x, reasoning_data, width, label='Reasoning', color='#2196F3', alpha=0.85, edgecolor='black', linewidth=1)
    ax.bar(x + width, negation_data, width, label='Negation', color='#FF5722', alpha=0.85, edgecolor='black', linewidth=1)
    ax.set_xlabel('Data Type', fontsize=14, fontweight='bold')
    ax.set_ylabel('Accuracy (%)', fontsize=14, fontweight='bold')
    ax.set_title('Data Type × Question Type', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([dtype_names[dt] for dt in dtypes], fontsize=13, fontweight='bold')
    ax.legend(loc='upper right', fontsize=12)
    ax.set_ylim(0, 110)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{BASE_PATH}/qtype_dtype_crosstab.pdf', dpi=200)
    plt.close()
    print("已生成: qtype_dtype_crosstab.pdf")
    
    # ===== 6. 模型×数据类型热力图 =====
    model_dtype_acc = {m: {d: 0 for d in dtypes} for m in models}
    for model in models:
        for dt in dtypes:
            correct = 0
            total = 0
            for task in data['tasks'].values():
                if task['model'] == model and task['status'] == 'done':
                    if sample_to_dtype.get(task['sample_id']) == dt:
                        correct += task['correct']
                        total += task['total']
            model_dtype_acc[model][dt] = correct / total * 100 if total > 0 else 0
    
    df = pd.DataFrame(model_dtype_acc).T
    df.columns = [dtype_names[d] for d in dtypes]
    df.index = [m.split('/')[-1].replace('-', '\n') for m in df.index]
    
    fig, ax = plt.subplots(figsize=(12, 9))
    sns.heatmap(df, annot=True, fmt='.1f', cmap='YlOrRd', vmin=55, vmax=95, ax=ax, 
                cbar_kws={'label': 'Accuracy (%)'}, annot_kws={'fontsize': 10, 'fontweight': 'bold'})
    ax.set_title('Model × Data Type Accuracy', fontsize=16, fontweight='bold')
    ax.set_xlabel('Data Type', fontsize=13, fontweight='bold')
    ax.set_ylabel('Model', fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'{BASE_PATH}/model_dtype_heatmap.pdf', dpi=200)
    plt.close()
    print("已生成: model_dtype_heatmap.pdf")
    
    # ===== 7. Thinking vs Instruct =====
    param_sizes = ['8B', '30B', '235B']
    inst_acc = []
    think_acc = []
    for param in param_sizes:
        if param == '8B':
            inst_model = 'qwen/qwen3-vl-8b-instruct'
            think_model = 'qwen/qwen3-vl-8b-thinking'
        elif param == '30B':
            inst_model = 'qwen/qwen3-vl-30b-a3b-instruct'
            think_model = 'qwen/qwen3-vl-30b-a3b-thinking'
        else:
            inst_model = 'qwen/qwen3-vl-235b-a22b-instruct'
            think_model = 'qwen/qwen3-vl-235b-a22b-thinking'
        inst_acc.append(model_acc.get(inst_model, 0))
        think_acc.append(model_acc.get(think_model, 0))
    
    fig, ax = plt.subplots(figsize=(10, 7))
    x = np.arange(len(param_sizes))
    width = 0.35
    ax.bar(x - width/2, inst_acc, width, label='Instruct', color='#9C27B0', alpha=0.85, edgecolor='black')
    ax.bar(x + width/2, think_acc, width, label='Thinking', color='#FF9800', alpha=0.85, edgecolor='black')
    ax.set_xlabel('Parameter Size', fontsize=14, fontweight='bold')
    ax.set_ylabel('Accuracy (%)', fontsize=14, fontweight='bold')
    ax.set_title('Thinking vs Instruct Mode', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(param_sizes, fontsize=13, fontweight='bold')
    ax.legend(loc='upper right', fontsize=12)
    ax.set_ylim(70, 95)
    for i, (inst, think) in enumerate(zip(inst_acc, think_acc)):
        ax.text(i - width/2, inst + 0.5, f'{inst:.1f}%', ha='center', fontsize=11, fontweight='bold')
        ax.text(i + width/2, think + 0.5, f'{think:.1f}%', ha='center', fontsize=11, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{BASE_PATH}/thinking_vs_instruct.pdf', dpi=200)
    plt.close()
    print("已生成: thinking_vs_instruct.pdf")
    
    # ===== 8. 思考时间与准确率关系（三个并排折线图）=====
    # 每个参数量的模型：按思考时间排序，分20百分位一组
    thinking_model_configs = [
        ('qwen/qwen3-vl-8b-thinking', 'qwen/qwen3-vl-8b-instruct', '8B'),
        ('qwen/qwen3-vl-30b-a3b-thinking', 'qwen/qwen3-vl-30b-a3b-instruct', '30B'),
        ('qwen/qwen3-vl-235b-a22b-thinking', 'qwen/qwen3-vl-235b-a22b-instruct', '235B')
    ]
    
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    
    for idx, (think_model, inst_model, param) in enumerate(thinking_model_configs):
        ax = axes[idx]
        
        # 收集该模型所有样本的思考时间和准确率
        samples_data = []
        for task_key, task in data['tasks'].items():
            if task['model'] == think_model and task['status'] == 'done':
                usage = task.get('usage', {})
                reasoning_tokens = usage.get('reasoning_tokens', 0)
                if reasoning_tokens > 0:
                    acc = task['correct'] / task['total'] * 100 if task['total'] > 0 else 0
                    samples_data.append({'tokens': reasoning_tokens, 'accuracy': acc})
        
        if len(samples_data) < 10:
            ax.text(0.5, 0.5, 'Insufficient Data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'{param} Model', fontsize=14, fontweight='bold')
            continue
        
        # 按思考时间排序
        samples_data.sort(key=lambda x: x['tokens'])
        n = len(samples_data)
        
        # 分成5个桶（每20百分位）
        n_per_bucket = n // 5
        bucket_means = []
        bucket_centers = []
        
        for i in range(5):
            start = i * n_per_bucket
            end = start + n_per_bucket if i < 4 else n
            bucket = samples_data[start:end]
            
            avg_tokens = np.mean([s['tokens'] for s in bucket])
            avg_acc = np.mean([s['accuracy'] for s in bucket])
            
            bucket_centers.append(avg_tokens)
            bucket_means.append(avg_acc)
        
        # 绘制折线图
        percentiles = ['P0-20', 'P21-40', 'P41-60', 'P61-80', 'P81-100']
        ax.plot(percentiles, bucket_means, marker='o', linewidth=2.5, markersize=10, 
                color='#2196F3', label='Thinking')
        
        # 获取instruct模型的整体准确率作为基线
        inst_correct = sum(t['correct'] for k, t in data['tasks'].items() 
                         if t['model'] == inst_model and t['status'] == 'done')
        inst_total = sum(t['total'] for k, t in data['tasks'].items() 
                        if t['model'] == inst_model and t['status'] == 'done')
        inst_acc_val = inst_correct / inst_total * 100 if inst_total > 0 else 0
        
        # 绘制基线虚线
        ax.axhline(y=inst_acc_val, color='#9C27B0', linestyle='--', linewidth=2, 
                   label=f'Instruct: {inst_acc_val:.1f}%')
        
        ax.set_xlabel('Thinking Time Percentile', fontsize=12, fontweight='bold')
        ax.set_ylabel('Accuracy (%)', fontsize=12, fontweight='bold')
        ax.set_title(f'{param} Model', fontsize=14, fontweight='bold')
        ax.legend(loc='upper right', fontsize=10)
        ax.set_ylim(60, 100)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{BASE_PATH}/thinking_time_analysis.pdf', dpi=200)
    plt.close()
    print("已生成: thinking_time_analysis.pdf")
    
    # ===== 9. 数据类型 × 思考长度与准确率（不按参数分组，合并展示）=====
    thinking_models = {cfg[0] for cfg in thinking_model_configs}
    fig, ax = plt.subplots(figsize=(9, 6.5))
    
    # 汇总所有thinking模型：按数据类型收集思考时间和准确率
    dt_data = {dt: {'tokens': [], 'acc': []} for dt in dtypes}
    for task in data['tasks'].values():
        if task.get('status') != 'done':
            continue
        if task.get('model') not in thinking_models:
            continue
        dtype = sample_to_dtype.get(task['sample_id'])
        if dtype not in dt_data:
            continue
        usage = task.get('usage', {})
        reasoning_tokens = usage.get('reasoning_tokens', 0)
        if reasoning_tokens <= 0:
            continue
        acc = task['correct'] / task['total'] * 100 if task['total'] > 0 else 0
        dt_data[dtype]['tokens'].append(reasoning_tokens)
        dt_data[dtype]['acc'].append(acc)
    
    avg_tokens = []
    avg_acc = []
    point_colors = []
    for i, dt in enumerate(dtypes):
        if dt_data[dt]['tokens']:
            avg_tokens.append(float(np.mean(dt_data[dt]['tokens'])))
            avg_acc.append(float(np.mean(dt_data[dt]['acc'])))
            point_colors.append(['#2196F3', '#4CAF50', '#FF9800', '#F44336'][i])
    
    if not avg_tokens:
        ax.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax.transAxes)
    else:
        for i, dt in enumerate(dtypes):
            if not dt_data[dt]['tokens']:
                continue
            ax.scatter(avg_tokens[i], avg_acc[i], s=170, c=[point_colors[i]], label=dtype_names[dt],
                       edgecolors='black', linewidths=1.5, zorder=5)
        
        # 趋势线（可选）
        if len(avg_tokens) >= 2:
            z = np.polyfit(avg_tokens, avg_acc, 1)
            p = np.poly1d(z)
            x_line = np.linspace(min(avg_tokens), max(avg_tokens), 100)
            ax.plot(x_line, p(x_line), 'r--', alpha=0.6, linewidth=2, label='Trend')
    
    ax.set_xlabel('Avg Thinking Tokens', fontsize=12, fontweight='bold')
    ax.set_ylabel('Avg Accuracy (%)', fontsize=12, fontweight='bold')
    ax.set_title('Data Type × Thinking Length vs Accuracy (Thinking Models)', fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{BASE_PATH}/thinking_dtype_all.pdf', dpi=200)
    plt.close()
    print("已生成: thinking_dtype_all.pdf")

    # ===== 10. 数据类型×题型热力图 =====
    dt_qtype_acc = np.zeros((len(dtypes), len(qtypes)))
    for i, dt in enumerate(dtypes):
        for j, q in enumerate(qtypes):
            if dt_qtype_total[dt][q] > 0:
                dt_qtype_acc[i, j] = dt_qtype_correct[dt][q] / dt_qtype_total[dt][q] * 100
    
    df_heatmap = pd.DataFrame(dt_qtype_acc, 
                               index=[dtype_names[dt] for dt in dtypes],
                               columns=[q.capitalize() for q in qtypes])
    
    fig, ax = plt.subplots(figsize=(10, 7))
    sns.heatmap(df_heatmap, annot=True, fmt='.1f', cmap='YlOrRd', vmin=50, vmax=95, ax=ax,
                annot_kws={'fontsize': 14, 'fontweight': 'bold'}, cbar_kws={'label': 'Accuracy (%)'})
    ax.set_title('Data Type × Question Type Heatmap', fontsize=16, fontweight='bold')
    ax.set_xlabel('Question Type', fontsize=13, fontweight='bold')
    ax.set_ylabel('Data Type', fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'{BASE_PATH}/dtype_qtype_by_model.pdf', dpi=200)
    plt.close()
    print("已生成: dtype_qtype_by_model.pdf")
    
    print("\n第五章所有图表生成完成！")

if __name__ == '__main__':
    generate_chap05_charts()
