# Pilot V3 结果分析

基于 40 条样本（四类各 10 条）× 6 道题 × 6 模型 = 1440 条评测记录。

---

## 一、数据来源效应（核心结论）

| 数据来源 | 准确率 | 样本量 |
|----------|--------|--------|
| **meaningful**（LLM 有意义） | **84.2%** | 360 |
| **real**（真实） | **81.9%** | 360 |
| **chaos**（完全混乱） | **65.6%** | 360 |
| **misleading**（误导） | **60.3%** | 360 |

**结论**：
- **有意义数据（real + meaningful）明显高于无意义数据（chaos + misleading）**，约 20+ 个百分点，与「流程图理解应依赖图示而非常识」的假设一致。
- **meaningful 略高于 real**：可能因 LLM 生成的图结构更规整、描述更完整，题目与图更对齐。
- **misleading 最低（60.3%）**：真实概念 + 错误组合的题最易触发「按常识答错」，说明误导类能有效测「看图 vs 凭常识」。
- **chaos（65.6%）高于 misleading**：完全混乱时模型可能更多乱猜或保守作答；误导类则容易被常识带偏，错得更稳定。

---

## 二、模型排序与 Thinking vs Instruct

**按模型总准确率（高→低）**：

| 排名 | 模型 | 准确率 |
|------|------|--------|
| 1 | qwen3-vl-235b-a22b-**thinking** | 82.1% |
| 2 | qwen3-vl-8b-**thinking** | 80.8% |
| 3 | qwen3-vl-30b-a3b-**thinking** | 77.5% |
| 4 | qwen3-vl-235b-a22b-instruct | 75.0% |
| 5 | qwen3-vl-8b-instruct | 62.9% |
| 6 | qwen3-vl-30b-a3b-instruct | 59.6% |

**结论**：
- **Thinking 系列整体优于同规模 Instruct**：8b/30b/235b 上 thinking 均高于对应 instruct，差距约 10–18 个百分点。
- **8b-thinking 超过 30b-instruct**：小模型+思考链在本任务上能弥补参数量差距。
- **30b-instruct 垫底**：与 8b-instruct 接近，可能在该任务上未充分受益于规模。

---

## 三、模型 × 数据来源（核心表）

| 模型 | real | meaningful | chaos | misleading |
|------|------|-------------|-------|------------|
| 235b-thinking | 85.0% | **91.7%** | 75.0% | 76.7% |
| 8b-thinking | **90.0%** | 86.7% | 73.3% | 73.3% |
| 30b-thinking | 86.7% | 88.3% | 70.0% | 65.0% |
| 235b-instruct | 80.0% | 81.7% | 76.7% | 61.7% |
| 8b-instruct | 75.0% | 76.7% | 55.0% | 45.0% |
| 30b-instruct | 75.0% | 80.0% | 43.3% | **40.0%** |

**结论**：
- **misleading 上区分度最大**：30b-instruct 40%、8b-instruct 45%，235b-thinking 76.7%，相差约 35 个百分点；说明「误导题」能拉开「凭常识」与「按图作答」的差距。
- **chaos 上 instruct 明显更差**：30b-instruct 43.3%、8b-instruct 55%，thinking 均在 70%+；无常识可依时，thinking 更稳。
- **real/meaningful 上各模型相对接近**：75–91%，说明在「正常图」上大家都能答得不错，差异主要体现在无意义类。

---

## 四、题目类型与难度

**按题目类型**（report 中模型×类型）：
- **factual**：各模型 76–84%，普遍最高。
- **negation**：30b-instruct/8b-instruct 仅 60–64%，thinking 系列 89–91%；否定题对 instruct 更难。
- **reasoning**：30b-instruct 55.1%、8b-instruct 57.8%，thinking 72–79%；多步推理上 thinking 优势明显。

**按难度**（stage_analysis 中）：easy 90%、medium 85%、hard 70%，难度分层有效。

**结论**：题型与难度设计有效；**negation 与 reasoning 是拉开模型差距的主要题型**，instruct 在这两类上明显弱于 thinking。

---

## 五、对实验设计的意义

1. **四类数据分层有效**：real/meaningful > chaos > misleading，支持全量实验按数据来源分层报告，并重点分析 misleading。
2. **模型选型**：thinking 系列在本任务上更稳，尤其是误导/混乱类；若要做「看图 vs 常识」的对比，建议保留 instruct 与 thinking 的成对比较。
3. **题目设计**：保持 pilot_v2 的 type/difficulty 设计（多跳推理、易混选项、否定题、hard 占比）是有效的，全量可继续沿用。
4. **样本量**：40 条 pilot 已能观察到稳定趋势；全量 1000 条可进一步做置信区间与显著性检验。

---

## 六、局限与注意

- **misleading 样本仅 10 条**：60.3% 的估计有抽样方差，全量 150 条后会更稳。
- **未控制题目在四类间的难度平衡**：同一套生成 prompt 下，chaos/misleading 的题可能偏难或偏易，全量可考虑按类型分层生成或事后平衡。
- **单次运行**：未做多次抽样/重复运行，报告为点估计；论文中可注明「pilot 结果，全量验证中」。

---

## 七、一句话摘要

**Pilot V3 表明：在流程图多选题上，（1）有意义数据准确率显著高于无意义数据；（2）misleading 最低且模型间差距最大，适合作为「看图 vs 常识」的评测维度；（3）Thinking 系列整体优于 Instruct，且在 negation/reasoning 与 chaos/misleading 上优势更明显；当前数据来源与题目设计可用于支撑全量实验。**
