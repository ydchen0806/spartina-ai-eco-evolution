# 厦大文献、外部数据与科学主线更新（2026-10-07）

已核实 7 篇论文的作者单位包含厦门大学环境与生态学院；不是根据作者姓名或关键词推断。核验依据是各论文 Crossref 作者单位、题名与摘要。New Phytologist 研究另读了原始数据仓库的实验方法。其余论文尚未完成全文逐段审查。

## 论文和数据线索

| 论文 | 对本项目的作用 | 数据进展 |
|---|---|---|
| [Ecology · 10.1002/ecy.3311](https://doi.org/10.1002/ecy.3311) | 开花物候：野外与共同园的纬度关系可不同 | metadata/abstract only; no raw table acquired for this paper |
| [Ecology · 10.1002/ecy.1815](https://doi.org/10.1002/ecy.1815) | 来源种群 × 环境交互；单一共同园不足以概括所有环境 | metadata/abstract only; no raw table acquired for this paper |
| [New Phytologist · 10.1111/nph.16371](https://doi.org/10.1111/nph.16371) | 原生地与入侵地：生殖与营养性状需分开检验 | 240 geographic and 720 greenhouse rows downloaded to project-local archive; methods read; raw and derived results withheld from public mirrors |
| [Functional Ecology · 10.1111/1365-2435.13384](https://doi.org/10.1111/1365-2435.13384) | 密度、个体大小与繁殖分配的自疏及异速关系 | 40 related DataCite records identified; relation is citation, not proof every dataset was analysed |
| [Molecular Ecology · 10.1111/mec.15192](https://doi.org/10.1111/mec.15192) | 遗传混合、互惠移栽和数量遗传共同支持机制判断 | metadata/abstract only; no raw table acquired for this paper |
| [Limnology and Oceanography · 10.1002/lno.11395](https://doi.org/10.1002/lno.11395) | 生物量纬度关系：环境可塑性与来源差异分开 | metadata/abstract only; no raw table acquired for this paper |
| [Journal of Ecology · 10.1111/1365-2745.12487](https://doi.org/10.1111/1365-2745.12487) | 早期野外纬度差异在共同园中多会减弱 | metadata/abstract only; no raw table acquired for this paper |

## 本次真正取得的数据

1. 厦大翔安校区共同园：GCE-LTER BOT-GCED-1912 的 240 条 2014 年野外记录、720 条 2015–2017 年共同园记录，附 EML 和两份详细方法。下载走来源单位的正式注册及下载流程。原始文件已保存在项目本地，SHA-256 已记录；仓库未提供独立文件校验值，不能把本地散列称为与提供者散列匹配。EDI 检索命中版本与 GCE 当前文件未作字节匹配，因此以实际下载的 GCE accession/1.0 为来源，不冒称获取了特定 EDI 修订版。
2. Georgetown 团队遗传空间数据：Tomasula 等，Frontiers in Genetics 2026，DOI 10.3389/fgene.2026.1810782；补充数据 DOI 10.3389/fgene.2026.1810782.s002。完整 ZIP 已下载，MD5 与提供者一致。不是厦大论文。其 935 个采样茎、223 个推定多位点谱系、10 个现场斑块，提供观察单位的外部实例。每斑块 5–45 个谱系；一个谱系跨两个斑块。使用作者提供的谱系分类，没有重做遗传聚类，不能用来推断本地影像的克隆身份。

## 文章应回答什么

当前最可检验的问题是：**克隆植物从孤立斑块进入连续植被的过程中，真实生态变化与观察单位改变分别贡献了多少表观生长和周转？**

影像为观测层；斑块并合、邻域竞争和更新为生态过程层；来源差异、克隆身份和跨环境适合度为进化证据层。AI 的职责是提供经过独立验证的物种覆盖和事件概率，以及在未来年份、独立地点上的增量预测能力。这三个层级不能靠模型分数直接相互替代。

Nature 级别的主张至少需要一种一般性机制在独立系统中得到有力证据。现有数据追溯和敏感性分析是基础，但单站点档案审计、引用顶刊和改善图形本身都达不到这个要求。文稿保留了未完成验证的标记。

## 下一轮实验的判别逻辑

| 竞争解释 | 可检验预测 | 首要测量与对照 | 支持机制前的门槛 |
|---|---|---|---|
| 观察与筛选 | 在相同空间范围纳入连续植被、非增长对象与不可见状态后，历史趋势改变 | 固定面积物种覆盖；独立事件标注；采样概率 | 配准误差与检测误差有独立估计 |
| 密度制约与并合 | 控制初始大小、环境和观测条件后，邻域占据及接触边界预测扩展与并合 | 预先定义邻域尺度；连续植被图；时间外推 | 并合与死亡能被独立区分，多个地点复制 |
| 环境可塑性 | 同来源材料跨盐度/淹水环境改变性状与扩展，来源排序可变 | 来源 × 环境的随机区组实验 | 环境处理真实重复；不把盆或图块当来源重复 |
| 遗传分化/适应 | 经标准化繁殖后来源差异仍保留；适合度的来源 × 环境效应符合预定适应预测 | 分型、克隆重复、共同园/互惠移栽、存活与繁殖 | 区分母体/携带效应、祖源与选择；单一花园不足 |

冻结的 32 地点 × 15 期 RGB 标注试验仍是第一优先级。现有专家标注数为零；不要用外部卫星类别或旧 mask 冒充独立真值，也不要在 test 图块上选择模型。实验样本量需由独立地点/来源层级的先导方差和目标效应决定，不填写没有依据的“足够样本量”。

## 新图与文稿

主图 2–4 统一为 183 mm 宽度，采用可区分色系、PDF/SVG 矢量输出及对应 CSV 源数据；预测图同时显示 R² 与 MAE，避免只展示有利损失函数。遗传单位新增 Extended Data Figure 8，所有十个斑块进入统计，示意空间图按最小/最大谱系数透明选择。审阅版将图和图注放在同页，PDF 优先嵌入 SVG，DOCX 保持可编辑正文。

核对的官方指南：
- https://www.nature.com/nature/for-authors/formatting-guide
- https://www.nature.com/nature/for-authors/final-submission

指南给出标准图宽 89/183 mm、图面正文 5–7 pt、面板字母 8 pt、线宽 0.25–1 pt，以及约 200 字的摘要和通常不超过 3,000 字的 Methods。当前新建统计图按这些尺寸重绘；旧的扩展数据图仍需最终逐图排版检查。没有把排版合规等同于达到录用标准。

## 分发状态

厦大 GCE 文件的 EML 标为 CC-BY-4.0，但下载页另列旧版 LTER 条款，限制原始数据转存，并要求分发衍生物时通知作者。当前原始表和新数值分析保留在项目本地；不向 GitHub/HF 公开转存，也未给作者发送消息。其他明确 CC-BY-4.0 的遗传数据保留完整署名与许可。详细本地分析报告在 `nature_manuscript/xmu_common_garden_20261007/REPORT_ZH.md`。
