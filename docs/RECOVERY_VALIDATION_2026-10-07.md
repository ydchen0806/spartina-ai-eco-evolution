# 原始影像恢复核验与下一阶段研究路线

日期：2026-10-07。原始输入位于服务器 `raw_inputs/recovered_local_20261006/`；本报告中的派生结果位于发布目录 `data/derived/recovery_20261007/`。这次核验更新了此前“原图、mask、标注缺失”的状态；38.65 GB 原始档案尚未纳入本次代码发布包。

## 已经独立验证的证据

| 核验项目 | 结果 | 能说明什么 |
|---|---|---|
| 逐文件重新读取并计算 SHA-256 | 1,001 个文件，38,654,767,408 字节，0 个失败 | 服务器文件与恢复清单一致；不等同于科学标注正确 |
| 15 期 RGB / mask 配对 | 均为 26,606 × 24,443；mask 只有 0/255 | 15 期分析输入已恢复 |
| 地理信息 | RGB 为 EPSG:4326，变换矩阵相同；mask 无 CRS | 不能仅靠尺寸或相同头信息证明真实配准，也不能直接将像素数标作平方米 |
| 两种标注交付格式 | 714 张图、9,234 个对象；714 张图尺寸及多边形集合全部一致 | 统一闭合点、顶点起点与方向后，交付内容对应 |
| 79 张 PNG 与多边形栅格化 | IoU 中位数 0.99650，最低 0.95294；无越界顶点及孤立 annotation ID | 是编码一致性检查，不是模型分割精度；边界栅格化规则可能产生差异 |
| 表格坐标与恢复 mask | 5,745 / 5,746 条有效观测的外接框坐标精确对应 | 原始 mask 与历史斑块表之间建立了直接证据链 |

完整的 `20151017sp.tif` 必须读取 `imagery_georeferenced/`；`numvis/` 下同名文件仅为 500 × 500。前两期文件名只有月份信息（2014-08、2015-08），不能将月初当作已知航拍日期。

## 坐标与面积：本轮新的可重现发现

在 2014 年发现的固定裁剪区域为整图行 `[4000, 22000)`、列 `[10000, 25000)`。固定该规则后，对其余 14 期进行检验，没有逐期拟合位移：

```text
整图行 = 历史 x + 4000
整图列 = 历史 y + 10000
历史 x/y 指外接框左上角，而非斑块质心。
```

2014 年 568 / 568 条匹配；其余日期 5,177 / 5,178 条匹配。这里的 5,746 是“斑块 × 日期”观测数，不是独立个体数或已验证的谱系数。匹配不证明跨期生物学身份，也不证明 RGB 与 mask 的空间配准精度。

独立计算外轮廓内的前景像素后，仅 1 条与旧面积完全相等，各期面积差的中位数约为 +0.36% 至 +2.73%。进一步比较三种计数方法：

| 面积计数方法 | 与历史面积精确相同的观测数 |
|---|---:|
| 外轮廓内完整前景计数 | 1 |
| 外轮廓内计数，但省略外接框最后一行和一列 | 5,647 |
| 整个外接框内前景计数，并省略最后一行和一列 | 5,744 |

第三种公式为 `count_nonzero(mask[y:y+h-1, x:x+w-1])`，此处 `x/y` 为 OpenCV 的列/行坐标。该数值复现强烈支持旧面积采用排除最大边界的矩形切片，而不是严格逐斑块面积。整框计数还可能包含附近其他斑块。尚未找到生成矩阵的完整原始实现，因此应称为“数值重建的提取规则”，不要声称已经定位到原脚本中的具体错误行。

剩余两条已单独导出到 `mask_patch_unresolved_records.csv`：源表零起始行 2051（20180729，旧面积 804）和行 2607（20190828，旧面积 321）。后者同位置外轮廓前景为 3,712 像素，差异远超切片边界误差；不能强行修补。原表保持不变，新面积目前是审计列，不能直接替换成论文“校正结果”。外轮廓计数仍可能包含嵌套前景，正式重建需要固定连通性、孔洞和嵌套区域处理规则。

## 对生态学主线的影响

总览显示，mask 主要标记孤立斑块，大块连续植被没有被完整纳入。不同日期的拼接影像还存在黑色孔洞和白色填充。现有“非黑像素比例”仅为检查指标，尤其无法排除 2021 年白色填充，不能作为有效观测面积。

因此，mask 总前景下降既可能包含真实斑块变化，也可能受到合并进入连续植被、筛选规则、覆盖范围、潮位或季节的影响。不能据此推断总入侵面积下降，更不能直接推断遗传适应或扩散—生长权衡。

建议将可检验的核心问题收敛为：**入侵前沿斑块表观增长与更新的变化，有多少来自环境响应，有多少来自密度与斑块合并，有多少在排除观测偏差后仍表现为可重复的种群差异？** AI 的作用是产生经独立验证的边界、事件和不确定度，并检验跨年份/地点预测；进化解释需要独立遗传或共同园证据。

## 下一阶段实验顺序与判据

1. **建立可比较的观测区域。** 从 RGB 建立包含黑/白填充、孔洞和拼接边缘的有效区域；抽取稳定地物检验跨期位移。保留逐期覆盖掩膜和共同覆盖区域，报告覆盖损失。RGB 与 mask 经人工抽查后再赋予 mask 地理参考；在适当投影或椭球面积计算下生成面积单位。
2. **重建斑块及事件。** 固定连通域定义，计算质心、面积、周长和邻域密度；审计旧表中两条异常及框内邻斑块污染。用重叠关系和影像复核区别延续、新生、死亡、分裂、合并、覆盖缺失。消失不得自动归为死亡，空间邻近不得自动归为亲缘。
3. **独立人工验证。** 在原始正射影像上按年份、大小、边缘/内部与植被密度分层，另抽不依赖旧 mask 的随机区域检验漏检。先固定样本和空间隔离，再盲标。以小规模双人标注试点估计方差后确定正式样本量；报告对象检出率、边界误差、面积误差和事件混淆矩阵。现有交付格式间的一致性不得用于替代这些指标。
4. **针对竞争解释建模。** 比较仅季节/潮位与观测误差、加入邻域密度/合并事件、加入环境变量的分层模型；按个体轨迹、空间块和年份处理依赖。插补、标准化、PCA 和模型选择均在训练折内进行；保留完整年份与地点的外部检验。现有 R²=0.178/0.394 的探索性留出结果尚不满足这一最终标准。
5. **外部数据按明确假设接入。** 优先核对航拍时刻及当地潮位站数据，连接潮位与可见斑块面积；时刻缺失时进行范围敏感性分析。用 Landsat/Sentinel 季节影像验证连续植被扩张与合并背景，并显式处理分辨率差异。重新检查气象数据坐标与变量单位：当前恢复影像位于约 117.404–117.433°E、23.913–23.937°N；此前 NASA POWER 点为 117.60°E、23.95°N，只能作为背景，未经空间核对不能当作当地直接测量。GBIF/OpenAlex 现有结果为发现性材料：4,584 是 API 报告总数，不能冒充已下载并清洗的完整样本。
6. **进化证据独立设计。** 若主张可遗传的生长/扩散差异，需要多个种群、共同园/互惠移栽、克隆身份或基因组数据，并控制母体效应及表型可塑性。当前影像可以支持生态过程研究，不能单独跨越这一证据门槛。Nature 正刊是目标，是否具备广泛机制与跨系统普适性要由上述结果决定。

仍缺分割 checkpoint、原始固定训练/验证/测试划分及 714 张标注对应的完整训练 RGB；七组旧情景输出的导出实现亦未恢复。这些限制不阻止从现有正射影像启动独立验证和新的可复现实验。

## 论文可用的阶段性文字

**Results — data provenance (draft).** We recovered 15 paired RGB orthomosaics and binary masks and independently verified the checksums of all 1,001 recovered files. A fixed crop convention inferred from the first survey reproduced the bounding-box positions of 5,745 of 5,746 archived patch-date observations across the 15 surveys. An exclusive-maximum bounding-box pixel count reproduced 5,744 archived areas, revealing a systematic distinction between the historical area measure and foreground counts within individual patch contours. These checks establish raster-to-table provenance, rather than segmentation accuracy or biological continuity between surveys.

**Methods — audit (draft).** Source files were read without modification. We counted mask values using raster windows, compared paired raster dimensions and metadata, and inspected downsampled overlays. We canonicalized polygon ring orientation, starting vertices and repeated closing vertices before comparing the two annotation deliveries. For 79 delivered PNG masks, polygon rasterization agreement was assessed separately from model performance. We tested a fixed ROI (rows 4,000–21,999; columns 10,000–24,999) using external contours and bounding-box joins, excluded ambiguous extracted keys, and retained unmatched observations for review. No per-survey translation was optimized after the first-survey coordinate hypothesis was fixed. Candidate area rules were then compared descriptively across the recovered archive; their agreement is not an independent model validation.

## 复现与图注

从 `nature_manuscript/public_release/` 执行（原始输入需单独在服务器可访问）：

```bash
python -m pip install -r requirements.txt
python analysis/verify_recovered_hashes.py --source ../../raw_inputs/recovered_local_20261006 --output data/derived/recovery_20261007
python analysis/audit_recovered_rasters.py --source ../../raw_inputs/recovered_local_20261006 --output data/derived/recovery_20261007
python analysis/audit_recovered_annotations.py --source ../../raw_inputs/recovered_local_20261006 --output data/derived/recovery_20261007
python analysis/reconcile_mask_patch_coordinates.py --source ../../raw_inputs/recovered_local_20261006 --output data/derived/recovery_20261007
```

脚本将表格与图写入指定输出目录。发布快照中的图另整理于 `figures/recovery_20261007/`。

**原图总览：** 15 期 RGB 与红色 mask 叠加，采用相同数组索引；为查看原始恢复情况的缩略图，不证明像素配准或完整植被检出。前两期仅知月份。

**坐标与面积核验图：** 上图为固定裁剪规则下的精确外接框匹配比例，灰色为提出规则的首期；下图为外轮廓前景计数相对旧面积的中位差。它描述面积定义差异，不是生态增长率。

**全图前景计数图：** 数值为二值 mask 像素总数，尚未校正覆盖范围和样本纳入规则，不可标作总入侵面积。
