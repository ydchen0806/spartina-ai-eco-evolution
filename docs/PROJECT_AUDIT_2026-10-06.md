# Spartina 项目审计与 Nature 主线（2026-10-06）

## 已经确认的项目资产

仓库里有多个历史稿件版本。最完整、可直接阅读的版本是
`230521paper/240102/paper/Chen et al 0419.docx`；较早的排版 PDF 是
`230117paper/220920_paper/Rapid adaptation to the external environment leads to suboptimal phenotypes in invasive plants evidence from a deep learning approach.pdf`。
项目的科学对象是福建漳江口互花米草（*Spartina alterniflora*）入侵过程，方法组合是 UAV 影像、语义分割、斑块匹配、Gompertz/空间回归以及机器学习反事实模拟。

进一步检查历史压缩包后，已经找到了一个此前遗漏的原始派生数据档案：

- `nature_manuscript/external_data/legacy_simulation_archive/230214simulation/raw_data.xlsx`：854 条记录，2014–2020 年，包含斑块 `size/X/Y`、34 个环境变量、`pca1–pca4`、观测 `growth_rate` 和 `growth_rate_simulation`；
- 同目录 7 个情景工作簿：`all_feature`、`temperature`、`precipitation`、`pressure`、`visibility`、`wind`、`other_feature`。

因此，当前项目有两套需要明确区分的数据产品：854 行的环境—增长模拟档案，以及 727 行的父斑块/距离记录。两者尚未能按坐标和面积直接逐行匹配，不能未经审计地拼接。

目前能在仓库中逐行复核的表包括：

- `new plaque info1.csv`：727 条记录，2014–2021 年，包含新斑块面积代理值、父斑块面积、距离和像素位置；
- `new plaque info.csv` 与 `new plaque info 2015-2021.csv`：同一批记录的删减或字段简化版本；
- `Vegetation samples.xlsx`：外部植被样点，13,059 行，主要是 2018 年山东沿海样点，含 *S. alterniflora* 与多个盐沼物种；
- 历史稿件中嵌入的图表和模型叙述；UAV 原图、mask、原始 ERA5/潮位下载文件、训练代码和完整模型仍没有随项目落盘，但环境变量和模型输出的派生工作簿已经找回。

我已经把可复核重分析写入 `nature_manuscript/analysis/reanalyze_spartina.py`。脚本下载并保存了两类明确标记的外部背景数据：NASA POWER 的漳江口点位气候序列（2014–2021）和 GBIF 中以 *Spartina alterniflora* 检索到的中国坐标记录（12 条）。这些数据只作为背景或外部验证候选，不替代原始 ERA5/UAV 数据。

## 可复核结果

854 行环境—增长档案按年为 113、338、138、59、50、75、81 条，覆盖 2014–2020。观测 `growth_rate` 的年度均值为 2.303、2.395、1.870、1.134、1.811、1.504、1.504；这与旧稿中“2014 年 2.303、2020 年 1.504”的数字一致。按年度均值做 Spearman 检验为 ρ = −0.714，n = 7 年，P = 0.071；因此可以报告为下降趋势的描述性证据，不能把记录级显著性当作独立年份的显著进化速率。

环境—增长档案中的 `growth_rate_simulation` 与观测值相关系数 r = 0.905，RMSE = 0.699，MAE = 0.464。这个模型拟合可以作为模型校准结果，但需要空间/年份留出验证后才能作为泛化性能。

我进一步对 854 行档案做了不依赖原模型代码的留出审计。用随机森林、ExtraTrees、Ridge 和均值基线比较后，最佳模型在留一年验证中的 R² 只有 0.178、RMSE = 1.383；在空间分块验证中 R² = 0.394、RMSE = 1.187。旧稿中的高拟合值不能直接当作外推能力，正式论文必须同时报告这些时间/空间留出结果。

727 条记录按年为 111、94、42、36、70、103、130、141 条。记录数本身不能当成种群数量，因为它同时受检测、边界和匹配规则影响。新斑块面积代理值的年度中位数在 2014–2021 年间为 312、376.5、236.5、412、492、284、330、234 像素，呈现强烈的非单调波动。

把 `size / father_S` 作为“新斑块与父斑块面积比”的描述性指标后，2014–2019 年的年度中位数从 0.0807 降到 0.0069；按年度中位数做 Spearman 检验为 ρ = −0.943，n = 6 年，P = 0.0048。这个信号可以作为“新记录相对于父记录变小”的探索性结果，但不能直接称为代际生长率下降：记录的产生机制、父斑块匹配规则和影像检测阈值都可能随年份改变。

数据质量审计发现 2020 年所有 130 条记录的 `father_S` 都是 29,992，2021 年所有 141 条记录的 `father_S` 也都是 29,992；2021 年 `distance` 还是同一个值。这是结构性平台值，不应进入 parent-normalized trend 或空间扩张推断。脚本已自动把这些年度标记为 audit flag，并从父斑块归一化趋势统计中排除。2014–2020 的距离代理中位数上升，但它同样可能受坐标尺度、父斑块候选池和边界饱和影响。

新发现的情景工作簿暴露出一个关键的可复核问题：7 个工作簿的 `pca*_simulation` 输入确实不同，但 `growth_rate_simulation` 向量逐行完全相同，均值都为 1.91885；另一列 `growth_rate_pred` 则随情景变化，均值为 1.961–2.157。当前应把 `growth_rate_pred` 视为候选反事实输出，把不变的 `growth_rate_simulation` 视为导出列或基准列，直到找回代码确认其定义。这个问题已经写入 `recovered_scenario_export_audit.csv`，在完成变量定义和独立重跑前，不应把情景差异解释为因果机制。

脚本输出的表、JSON 审计和图在：

- `nature_manuscript/tables/patch_records_audited.csv`
- `nature_manuscript/tables/patch_year_summary.csv`
- `nature_manuscript/tables/reanalysis_audit.json`
- `nature_manuscript/tables/recovered_raw_growth_environment.csv`
- `nature_manuscript/tables/recovered_growth_year_summary.csv`
- `nature_manuscript/tables/recovered_scenario_export_audit.csv`
- `nature_manuscript/tables/model_holdout_summary.csv`
- `nature_manuscript/tables/model_holdout_predictions.csv`
- `nature_manuscript/tables/model_holdout_audit.json`
- `nature_manuscript/figures/generated_candidates/fig_patch_dynamics_audit.pdf`
- `nature_manuscript/figures/generated_candidates/fig_gbif_external_context.pdf`
- `nature_manuscript/figures/generated_candidates/fig_recovered_simulation_audit.pdf`
- `nature_manuscript/figures/generated_candidates/fig_model_holdout_audit.pdf`

## Nature 正刊应该采用的科学主线

建议把中心问题改成：**入侵种在新环境中是否会从“快速扩张”转向“环境容忍度优先”，以及我们能否用可审计的 AI 空间观测在野外重建这一转变？**

这条主线比“深度学习首次用于进化生态学”更有科学内容，也避免把算法新颖性当成生物学发现。文章需要把三个层次严格分开：

1. **观测层**：AI 从 UAV 影像中识别斑块、估计面积、匹配跨年对象，并量化检测不确定性。
2. **生态层**：斑块增长、扩张距离和环境响应是否发生时空变化。
3. **进化层**：只有在共同花园、移植、谱系/基因组或跨地点重复证据支持时，才能把生态型比例变化称为遗传或表观遗传适应。现有项目最多支持“与选择一致的表型转变”或“选择假说”，不能单凭空间回溯证明遗传性。

建议标题：**An aerial AI observatory reveals a shift from expansion to environmental tolerance in an invasive cordgrass**。如果后续没有独立遗传或共同花园实验，正文避免 `heritable`、`ecotype`、`genomic adaptation` 和 `causal`，改用 `phenotypic strategy`、`selection-consistent shift`、`environmental sensitivity`。

## 建议的主文图序

**Fig. 1 | 可审计的野外 AI 观测系统。** 研究区、年度正射影像、人工标注与空间留出验证；报告 mIoU、IoU、precision/recall、面积偏差和不确定性，而不是只报一个 VOI。训练/测试必须按空间块或年份拆分，禁止相邻 patch 泄漏。

**Fig. 2 | 扩张是否减速。** 显示检测校正后的占据面积、独立斑块数、斑块面积分布和新斑块距离；每个年度给出原始点、置信区间和检测概率。将“记录数”与“种群数量”分开。

**Fig. 3 | 环境敏感性随时间和空间变化。** 用层级时空模型或带空间随机效应的 GAM/GLMM 估计温度、降水、淹水/潮位对增长参数的响应；PCA 只作为降维，不把 PC 名称直接当作机制。报告空间留出预测、效应方向、尺度和不确定性。

**Fig. 4 | 反事实模拟与机制边界。** 用冻结模型做“观测气候 vs 稳定气候 vs 极端波动”的反事实，展示完整预测分布和校准误差。把这一图表述为模型条件下的反事实，不称为真实因果实验。

**Fig. 5 | 独立验证与进化检验。** 用外部地点或独立年份验证遥感推断；GBIF 只能做粗粒度出现记录背景。真正的进化证据应来自共同花园/ reciprocal transplant、亲本—子代繁殖值、基因组/甲基化或至少跨地点重复的性状遗传率估计。

## 必须先修正的逻辑与方法问题

- **遗传性越界**：空间上逐年增加的聚类类型不等于遗传生态型。正文要区分 temporal sorting、塑性、检测改变和遗传选择。
- **代际定义不成立**：把“某年新出现的 patch”直接当成一代需要繁殖史或年龄标记；应改称 annual cohort/record cohort，除非补充实验证据。
- **检测误差未进入统计模型**：IoU 81% 与匹配率 95.87% 不能自动保证面积趋势无偏。需要人工复核子样本、面积校准曲线、阈值敏感性和 occupancy/detection correction。
- **空间伪重复**：同一地点的多年 patch 不能按独立样本进入普通 ANOVA；应使用 patch lineage、空间 block、年份随机效应和 cluster-robust CI。
- **MGWR 不能证明因果**：局部回归回答空间异质性，不回答环境改变导致进化。应报告带宽、共线性、残差空间自相关、留一地点预测和多重比较控制。
- **机器学习验证需防泄漏**：模型 R² 不能只来自随机划分。必须提供空间/年份外推性能、预测区间、校准图、基线模型和消融实验。
- **时间范围和数据不一致**：稿件多处写 2013–2022、2014–2021 或 96/34 个气候变量；最终版本必须建立一张数据字典，逐项列出覆盖年份、样本数、原始来源、处理和缺失值。
- **像素面积没有物理单位**：必须给出 GSD、投影和 pixel-to-m² 校准；否则只能写 area proxy。

## 下一阶段实验优先级

### P0：恢复原始证据链（没有它不能投稿）

1. 找回所有年度 UAV 正射影像、人工 polygon/mask、patch ID、匹配表和 GSD/坐标参考，并把 854 行档案与 727 行档案按原始 ID/坐标映射。
2. 找回 ERA5-Land/潮位原始矩阵、下载日期、空间抽样方式和气候变量字典，核对 854 行中的 34 个变量是否为原始值、插值值或标准化值。
3. 找回 SegFormer/FPN 权重、训练/验证划分、随机种子、推理阈值和人工 QC 记录。
4. 重跑 7 个情景模型并逐行保存预测结果，确认情景输入改变时输出是否改变。
5. 将每个主文数字映射到 raw → model output → summary → figure/table 的唯一链路。

### P1：重跑 AI 与空间生态统计

1. 用空间 block 和留一年验证重训分割模型；补充面积 bias、boundary F1、patch-level precision/recall。
2. 对每年随机抽取人工复核 patch，拟合误差校正模型；用 occupancy/detection 模型估计真实出现概率。
3. 用 patch lineage 的层级模型估计年度增长，加入初始面积、空间随机效应、年份效应和检测概率。
4. 用 SHAP/Permutation importance 作为解释工具，主结果用可解释的部分效应和不确定性表达。

### P2：把“适应”变成可证伪的实验

1. 从早期与晚期 cohort 取亲本，在共同花园比较增长、盐度/温度/淹水胁迫和繁殖输出。
2. 做 reciprocal transplant 或至少多地点 common garden；估计 cohort × environment 交互和遗传率。
3. 若有材料，做低深度重测序/GBS 或靶向甲基化，测试表型策略转变是否有遗传/表观遗传对应。
4. 预注册 primary endpoint：环境胁迫下存活/生物量、增长衰减参数和环境敏感性；保留所有 cohort、地点和失败样本。

### P3：跨地点与遥感外部验证

优先扩大到中国沿海 3–5 个独立河口，用 Sentinel-2/Landsat 进行低分辨率趋势验证；GBIF/iNaturalist 记录只用于出现背景和采样偏差说明。外部验证必须保留 site-held-out 结果，不能选择最漂亮的地点。

## 建议的 Results 语言（当前证据可用版本）

> Across 727 patch records from 2014–2021, the median area of newly recorded patches relative to their putative parent patch declined between 2014 and 2019. Because parent-patch sizes were structurally constant in 2020 and 2021, those years were excluded from parent-normalized trend estimates. This pattern is consistent with a shift in the spatial phenotype of newly recorded patches, but it does not by itself establish generational change, heritability or a causal environmental mechanism.

## 交付状态

本轮已经完成：原始目录扫描、历史压缩包恢复、854 行环境—增长档案重分析、情景输出审计、727 条父斑块记录审计、NASA POWER/GBIF 外部数据下载、年度汇总、候选主图和 Nature 主线 briefing。下一步最有价值的工作是恢复 P0 原始证据、核对 `growth_rate_pred` 与 `growth_rate_simulation` 的定义并完成空间留出验证；否则任何“快速进化/遗传适应”的强表述都无法通过严格审稿。
