# 找到并取得同一区域的20厘米无人机数据（2026-10-07）

之前未取得的是 **Site10 对应论文的原始影像和逐样方数据**：其公开附件只有一份汇总DOCX，全文说明原始数据向作者申请。此前检索没有充分追溯同区域的独立数据论文。本轮扩大到地名、作者、数据论文和正式存储记录后，找到了厦大团队公开的漳江口无人机档案，并已完整下载、校验和分析。

## 实际取得

Huang、Zhang、Zhou、Zhu，ScienceDB V4：[10.57760/sciencedb.o00119.00069](https://doi.org/10.57760/sciencedb.o00119.00069)。关联数据论文：[10.11922/11-6035.csd.2023.0011.zh](https://doi.org/10.11922/11-6035.csd.2023.0011.zh)。对应作者的机构记录包含厦门大学。

- **10幅RGB正射影像＋10幅互花米草分布图，共20个完整原始TIFF，1,844,072,803 bytes。**
- **20厘米分辨率**，WGS84/UTM50N；十期为2013-08、2014-08、2015-08、2016-11、2017-11、2018-11、2019-12、2020-12、2021-12、2022-06。
- 十幅分布图的完整外接矩形都位于我们恢复的完整影像范围内，已按CRS转换核对，不只是同一县市。
- 2021-12和2022-06的RTK命名产品增加了原15期序列没有的拍摄月份。RTK文件名本身不证明实际配准精度。
- 每个文件均核对提供方MD5和大小，另生成SHA-256。全部原件已上传HF，并核对远端LFS SHA-256。

[HF原始档案](https://huggingface.co/datasets/cyd0806/spartina-ai-eco-evolution-data/tree/main/external_sources/zhangjiang_uav_20261007) · [逐文件校验清单](../external_data/zhangjiang_uav_20261007/download_manifest.json)

本次通过公开网页使用的文件目录接口取得V4文件清单，再走官方公开下载链接，无需作者邮件或私有账户。此前根目录请求为空并不表示文件不存在：该存储的版本根目录是 `/V4`，下面有 `DOM` 和 `Spartina alterniflora data` 两个目录。没有绕过权限限制。

许可为 **CC-BY-NC-SA-4.0**，并非CC-BY或MIT。原始数据和我们的衍生图表保留署名、非商业与相同方式共享要求。代码许可不改变数据许可。

## 原始影像的同源性已经检查

2014-08、2015-08的公开影像与恢复影像投影到相同诊断网格后，灰度相关分别为 **0.999073、0.998879**。SIFT匹配中分别有1769/1773和3104/3104对与近单位仿射变换一致。这种近乎一致的图像结构支持“同源或相近处理版本”的解释，不能作为独立站点或新增训练测试样本计数。飞行原片与处理记录仍未核对。

[来源对应审计](../data/derived/zhangjiang_uav_20261007/source_correspondence/source_correspondence.json) · [2014对照](../data/derived/zhangjiang_uav_20261007/source_correspondence/201408_public_recovered_comparison.jpg)

原来的恢复档案并未因此获得失踪的分割checkpoint、固定训练划分或714张训练RGB照片；这是另一套已发表正射影像与分布产品，不能把“数据获得”写成“原分割模型已复现”。

## 已完成的新分析

**固定观测范围内的景观标记面积。** 将所有十期RGB有效覆盖与分类图矩形取交集，得到固定 **248.935 ha**；与历史ROI的交集为211.60 ha。在相同范围内比较，避免把覆盖边界改变算作扩张。

| 航期 | 共同范围内的标记面积（ha） |
|---|---:|
| 2013-08 | 21.35 |
| 2014-08 | 28.93 |
| 2015-08 | 41.23 |
| 2016-11 | 62.16 |
| 2017-11 | 75.29 |
| 2018-11 | 100.21 |
| 2019-12 | 105.79 |
| 2020-12 | 103.76 |
| 2021-12 | 111.81 |
| 2022-06 | 122.82 |

原始20厘米前景像元精确计数与1米分数网格全幅面积最大差0.000758 ha。分数网格平均时显式保留零值，不能让软件把零当NoData剔除后错误地产生全为1的面积比例。分析脚本同时输出原生计数、固定范围和近似误差。

**新增航期的标记变化。** 2021-12与2022-06分类数组尺寸和分辨率相同，坐标原点仅差0.0001093 m。在两期RGB都有效的250.163 ha内，20厘米原生数组配对得到：保留正类标记111.697 ha，移除正类标记0.305 ha，新增正类标记11.326 ha。

这里存在必须保留的解释限制：分类图的0明确标记为NoData，未证实为物种缺失；“新增/移除”指地图标签，不能称为招募、死亡、根除或替代。两期跨越12月和6月，季节、潮位、配准和分类规则仍可能影响比较。数据说明称主要在白天低潮飞行，但没有逐航期的精确潮位。本轮读了官方数据说明和数据论文的索引摘要，未取得完整数据论文Methods，因此不臆测分类算法或独立精度。

[新四联图PNG](../data/derived/zhangjiang_uav_20261007/zhangjiang_uav_extension.png) · [矢量PDF](../data/derived/zhangjiang_uav_20261007/zhangjiang_uav_extension.pdf) · [固定范围源表](../data/derived/zhangjiang_uav_20261007/common_footprint_positive_area.csv) · [标记转移表](../data/derived/zhangjiang_uav_20261007/endpoint_label_transitions.csv)

## 对科学问题和文章的改进

新增数据使我们能够检验：**孤立斑块记录中的表观增长变化，是否伴随斑块并入连续植被，而整个景观仍持续被占据？** 这是比直接把“年份—增长率”相关解释成快速进化更可检验的生态问题。

工作稿新增本地UAV Results、完整处理Methods、来源同源性诊断、数据可用性、两条参考文献及Extended Data Figure10。图中明确区分原始影像、分布标签与生物学事件。现有数据支持景观尺度的标记面积序列；要检验融合机制，下一步须在新增RTK影像上确认配准误差、对消失/融合候选做独立人工判读，并与已有斑块轨迹连接。

同一轮还取得了漳江口2007/2008年盐度梯度与植株高度、密度、横向扩张的公开汇总表（Zhang et al.2012，Ecology93:588–597，Appendix C，Figshare3552801，CC0），用于机制背景。原附件标题写2007，存储标题写2008；已记录冲突，未自行消解。它是均值±SE，不是逐个体原始数据，也没有足以证明本地样方重叠的坐标，不做额外独立重复计数。

Site10（2025年）的原始材料依然未公开取得，本轮无人机档案来自另一篇数据论文。两者的日期、来源和许可在文件中分别记录。尚未联系任何作者。

## 复算

```bash
python analysis/download_zhangjiang_uav.py --output /path/to/zhangjiang_uav
python analysis/analyze_zhangjiang_uav.py --source /path/to/zhangjiang_uav --output data/derived/zhangjiang_uav_20261007
python analysis/compare_zhangjiang_source_imagery.py --source /path/to/zhangjiang_uav --recovered /path/to/recovered/imagery_georeferenced --output data/derived/zhangjiang_uav_20261007/source_correspondence
```
