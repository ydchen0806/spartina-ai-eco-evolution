# 增长指标、轨迹与观测缺失：第二阶段实证审计

本轮从恢复影像推进到论文分析单位与响应变量。原文件保持不变；全部新结果位于 `data/derived/trajectory_audit_20261007/`，原图复核包位于 `figures/transition_review_20261007/`。本报告补充同日的恢复核验报告。

## 1. 论文响应变量的定义影响年度趋势

年度面积矩阵 `result_size1229.csv` 有2,459行，其中1,769行只出现一次。按行连接相邻有效年度，得到957条年度转移，年度标签间隔均为1年；这不意味着航拍间隔恰好365天。

`mydata_0224.xlsx` 的854条模型记录全部能按 `(year, size, growth, 下一期X, 下一期Y)` 追溯到这些转移，保留重复键的出现次数。其中4条存在多重候选，不强行认定唯一轨迹身份。

设初始面积为 A₀、下一期面积为 A₁。矩阵与模型表满足 `growth = A₁ − A₀`；但模型中的 `growth_rate` 并非所有年份都等于 `(A₁ − A₀) / A₀`：

| 起始年份 | 模型记录数 | 不一致数 | 原 growth_rate 均值 | 同样本面积重算均值 |
|---|---:|---:|---:|---:|
| 2014 | 113 | 0 | 2.303079 | 2.303079 |
| 2015 | 338 | 0 | 2.394670 | 2.394670 |
| 2016 | 138 | 138 | 1.869924 | 0.880595 |
| 2017 | 59 | 0 | 1.133872 | 1.133872 |
| 2018 | 50 | 50 | 1.810842 | 2.569990 |
| 2019 | 75 | 0 | 1.504079 | 1.504079 |
| 2020 | 81 | 0 | 1.504407 | 1.504407 |

数值比较容差为1e−8。2016年的原值比面积重算值高0.179–1.804；2018年低0.150–1.171。转换原因尚未找到，不应推测为有意修改或自动认定为计算错误；年化、季节校正等解释需要原公式支持。

具体可追溯例子：零起始模型行494与498都对应2016年、初始面积5,598、增量8,064、下一期坐标(5,750, 10,087)，面积重算相对增量均为1.440514，但存储的 growth_rate 分别为2.178245和1.969595。这说明仅有这几个几何字段还不能解释存储值。完整对照位于 `model_endpoint_trace.csv` 与 `ambiguous_endpoint_links.csv`。

保持854条样本不变，7个年度均值与年份的 Spearman ρ 从原值−0.714（P=0.071）变为面积重算值−0.107（P=0.819）。纳入全部957条转移时，面积重算年度均值的ρ为−0.607（P=0.148）。均为7年描述性比较，不能将任何版本称为已建立的时间机制；全部样本均值还易受很小初始面积对应的极端比值影响。原趋势本就没有达到常用的0.05阈值，本轮结果进一步显示它对指标和筛选定义敏感。

面积重算沿用历史面积，不是经过独立标注验证后的真值；它仅隔离响应变量定义的影响。此前发现的边界切片与邻斑块计数问题还需另行处理。

## 2. 筛选与位置字段已经数值重建

854条模型记录恰好等于从957条转移中保留 `0 < (A₁ − A₀)/A₀ < 10` 的记录。其余103条由50条非正增长和53条相对增量至少为10的记录组成。此结论是对归档表的数值重建，尚不能替代缺失的完整生成脚本。

因而，当前模型拟合的量应描述为“被追踪且通过增长筛选的斑块的条件增长”，不能解释成全种群增长、死亡率或总体入侵速度。消失斑块、合并、单次观测和非正增长均不能从模型样本中恢复为无偏总体估计。

854条模型位置都来自下一期外接框，只有2条同时也与初始外接框相同。若任务定义为预测未来增长，下一期坐标及由其计算的空间变量需要检查是否引入未来信息；若任务是回顾性关联，应明确变量的时间归属。不能不经核查就断言所有环境变量均存在泄漏。

年度矩阵与15期矩阵也不是完全相同的观察版本：2014、2015的年度观测全部对应各自8月影像；2016最多对应10月25日（448/459）、2017对应7月28日（322/325）、2018对应7月29日（322/323）、2019对应8月28日（293/293）、2020对应7月27日（316/317）、2021对应7月17日（285/286）。剩余差异列为待追溯，不能给所有年度记录直接套用一个精确拍摄日。前两期仍只有月份信息。

## 3. 连通斑块重建与轨迹筛查

在固定ROI内，以8邻域建立连通域，得到15期共8,280个连通域（含很小区域）。每期连通域面积之和与上轮独立计算的前景像素总数完全相同；此校验避免外轮廓框内混入其他独立对象。旧表5,746条观测中5,745条能按外接框左上角连接到连通域。

但相同日期的一个连通域可能被多行历史轨迹使用：80个“日期×连通域”对应167条表格观测，超出唯一对象数87条。需要审计是否为合并后的多条轨迹共享终点、复制记录或其他匹配规则，不得当作独立个体。见 `shared_components.csv` 和 `shared_component_archive_records.csv`。

对相邻影像，在未重新配准的数组索引上计算连通域交集。主筛查要求两侧面积≥100像素、交集≥10像素、交集/较小斑块面积≥0.25。前14期共5,459条源观测的结果为：

| 历史记录与掩膜关系 | 记录数 |
|---|---:|
| 历史行延续，指定后继斑块通过重叠筛查 | 1,386 |
| 历史行延续，指定后继未通过重叠筛查 | 1,123 |
| 下一期历史行缺失，但存在其他 mask 重叠对象 | 177 |
| 下一期历史行缺失，也没有通过筛查的 mask 对象 | 2,772 |
| 源外接框无法唯一重建 | 1 |

这些是记录层面的候选关系，含共享斑块记录；不是独立生物个体的事件计数。1,123条未通过重叠筛查也不能直接称为追踪错误，位移、边界变化、配准误差或追踪错误均可能造成这一结果，其中37条存在其他可重叠目标。

将重叠阈值改为0.10/0.25/0.50，候选边数为2,124/1,781/1,188，多对一候选目标数为52/31/16，多后继候选源数为41/21/10。这些结果对阈值与配准敏感，尚不能作为已验证的合并/分裂率。

## 4. 观测缺失与配准：当前不能自动给出死亡标签

80条没有下一期历史行的记录，其源斑块像素对应的下一期RGB中至少95%为精确黑色或白色：58条发生在2015-10→2016-09，22条发生在2018-08→2018-09。该筛查是填充诊断，不是权威覆盖图。已查看的示例（例如 `case_010`）下一期为完整黑色缺口，表明观测缺失确实存在。其他案例仍需逐个复核；缺失首先应保留为不可观测候选，不能直接编码为生物死亡。

额外运行了固定16个空间窗口的SIFT双向匹配与比值筛选。部分仿射模型只在棋盘格一半窗口拟合，另半窗口检查残差。14组相邻日期只有6组达到诊断拟合所需的匹配数量；这6组的留出残差中位数约4.5–164.9像素。仅1组的中位数低于5像素，且其5像素内留出匹配比例仅54.5%。描述性筛查门槛（至少3个训练内点窗口、≥80%留出匹配在5像素内且留出中位数≤5像素）没有任何日期对通过；该门槛并非预注册实验。

特征可能包含变化植被、潮滩或误匹配，训练内点还可能集中在少数空间窗口。因此，这不是已建立的配准误差真值，也不是可直接应用的校正变换。**本轮没有用这些拟合移动原图或 mask，也没有据此改写生态事件。** 下一步需要覆盖研究区的稳定地物控制点，并在独立地点验收，而非仅依赖相同GeoTIFF头信息。

## 5. 已交付的人工复核材料

`figures/transition_review_20261007/index.html` 可在浏览器中打开，默认显示原图，勾选后显示粉色 mask。固定种子20261007；每个源日期×自动筛查类别抽1条，并额外抽至多4条高填充记录，共61组、122幅前后期组合图。

每组先看原图，再查看叠加层；窗口以源斑块外接框中心为中心，前后期保持同一像素窗口，尚未配准。配套提供空白复核CSV及精确窗口位置清单。所有专家标签仍为空；本轮查看的少量示例是发现问题用的视觉检查，不能冒充盲法专家验证。类别富集抽样不能估计事件发生率，正式检出性能仍需包含旧mask阴性区域的概率抽样。

## 6. 对文章和下一轮实验的具体调整

本轮不新增“快速适应”或“进化权衡”的结论。将旧年度下降、情景模拟与环境机制解释保留为待验证结果；论文核心应先明确真实响应变量与观察过程。

下一轮按以下顺序推进：

1. 追溯2016/2018响应变量转换。保留原列与面积重算列，查验日期、单位和是否有年化/季节校正；找不到转换时不得把不同定义混为同一响应量。
2. 冻结稳定地物控制点及空间留出区域，复核61组诊断样本；先解决跨期配准与缺测，再给出跨期事件标签。
3. 明确一个mask对象对应多条历史行时的分支规则，重建具有唯一对象标识、允许合并/分裂、显式记录不可观测状态的轨迹图。用独立RGB标注检验事件与边界精度。
4. 新AI实验同时报告两类任务：观测/事件识别，以及在明确风险集中的增长预测。使用初始时刻可获得变量；原始气象特征的插补、标准化及降维放在训练折内。旧掩膜可作训练候选，但独立测试标签必须来自冻结的RGB样本；验证泄漏与同一斑块多行重复须先消除。
5. 生态检验比较环境响应、邻域拥挤和合并退出样本等竞争机制；解释全种群动态需要纳入负增长与不可观测状态。遗传适应仍需共同园、移栽或遗传证据。

当前最有价值的科学问题是：在一个斑块不断生长、合并并改变可观测性的入侵系统中，如何区分观察到的增长变化与真实人口统计过程变化？只有观测误差得到独立验证后，才进一步检验环境和进化机制。这是研究路线，不是本轮已经证明的新机制。

## 7. 论文阶段性英文文字

**Results draft — endpoint and observation sensitivity.** All 854 records in the archived modelling table could be linked by year, initial area, area increment and subsequent bounding-box position to annual matrix transitions, preserving the multiplicity of repeated records. The retained set was numerically equivalent to selecting relative area increments between zero and ten from 957 archived transitions. Stored growth endpoints differed from area-derived relative increments for all 138 records starting in 2016 and all 50 records starting in 2018. Holding the record set constant, the Spearman correlation between year and annual mean endpoint changed from −0.714 to −0.107 when the endpoint was recomputed from archived areas. The undocumented transformation and observation filters therefore require resolution before interpreting temporal differences mechanistically.

**Methods draft — raster transition audit.** Binary masks were decomposed into 8-connected components within the previously reconstructed region of interest. Component pixel counts were checked against independent raster foreground totals. Adjacent-survey overlaps were screened at three thresholds of intersection divided by the smaller component area (0.10, 0.25 and 0.50), conditional on component areas of at least 100 pixels and intersections of at least 10 pixels. These unregistered overlaps were treated as review candidates, not demographic events. Exact black or white RGB values at preceding component locations were used to flag possible observation gaps. An enriched diagnostic sample was exported for subsequent human review; it was not used to estimate event prevalence or segmentation accuracy.

**Figure captions.** Growth-endpoint sensitivity: stored and area-derived annual means for identical model records, the corresponding record-level comparison, and archived versus retained pair counts. All values remain conditional on historical tracking and area extraction. Alignment diagnostic: residuals for matched image features in spatially held-out tiles, before and after a transform fitted elsewhere; missing points indicate insufficient matching support. Features are not independently surveyed ground control.

## 8. 复现

在发布目录运行：

```bash
python analysis/audit_growth_endpoint.py --output data/derived/trajectory_audit_20261007
python analysis/audit_mask_transitions.py --source ../../raw_inputs/recovered_local_20261006 --output data/derived/trajectory_audit_20261007
python analysis/diagnose_image_alignment.py --source ../../raw_inputs/recovered_local_20261006 --output data/derived/trajectory_audit_20261007
python analysis/summarize_trajectory_audits.py --audit data/derived/trajectory_audit_20261007
python analysis/build_transition_review_pack.py --source ../../raw_inputs/recovered_local_20261006 --audit data/derived/trajectory_audit_20261007 --output figures/transition_review_20261007
```

大型连通域步骤需数GB工作内存。软件版本与上一轮恢复核验环境相同。所有坐标与面积保持像素单位；不把未验证的地理参考换算为已知精度的平方米或位移米数。
