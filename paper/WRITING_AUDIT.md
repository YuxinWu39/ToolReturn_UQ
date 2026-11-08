# 初稿写作核验（2026-11-08）

范围：当前研究材料转写为 venue-neutral 英文工作稿；没有新实验、训练或模型请求。使用 scientific-critical-thinking 作问题/单位/主张核对，使用 anti-ai-writing 作引用、措辞和具体性检查。不套用临床 RoB/GRADE，不把模型自评当作统计证据。

## 主张与来源

- 接受决策对照来自两份固定 pilot summary；保留 invalid 在主分母中，说明 valid-pair sensitivity 已归档。主对照是 clean-minus-corrupted acceptance 的 context 差，不与 AUROC 混写。
- 相同可见样本的统计检测来自 F11 锁定 summary；只导出通过 context sanity 的真实检测 AUROC；head5/random20 四项失败门槛保留在附录。
- 独立行抽样来自 F12 summary；明确 240 query/draw 单位仍是 12 查询、6 表，没有新的模型回答。严重度绑定查询、方向绑定表，均没有因果幅度推论。
- 原始与行抽样 AUROC 的估计对象不同，不把两数差称作性能下降或原样本偏差。
- 0d 公式、分母 floor、EPS、B=2000、20% failed-resample 规则与源代码核对一致。相同 raw rows 仍有结构化输入和计算量差异。
- P5 六组配置的真实污染增益 withheld；H1 版本冲突和缺少 live sanity 保留；0o/0o* 没有最优性证明。
- Qwen 72 条 raw 与 Gemini 72 条 raw 均已核验；历史审计的旧缺档句仅代表当时快照，当前稿不沿用该限制。

`export_paper_evidence.py --check` 验证 18 项证据、7 个来源哈希、7 张生成表；JSON pointer 保留机器可追溯位置。其覆盖范围是导出字段与表格，不自动验证所有叙述。正文中的主数字、模型配置、格式失败分类、置信度语义诊断与已保存材料逐项核对。

## 引用核对

Xu v2 的 Qwen3-8B、content likelihood 与 legal-action entropy 定义，ToxicBench v1 的 evidence controls，分别核对官方原文；不声称首次研究 tool boundary 或首次发现错误采纳。Efron 的 bootstrap 原始文献使用出版社 DOI。Kassis 引用核对当前官方 arXiv 的作者/标题/年份，使用不带版本后缀的 DOI。六项数据集的署名/DOI 从官方数据资源核对，版本化 CSV 行数和 SHA 来自本地 provenance。

此处只做最近邻与引用匹配核验，不构成穷尽文献检索或新颖性证明。近邻两篇 2026 文献均明确标为 arXiv preprint。没有从旧 50 项 bibliography 自动导入未经本轮核对的条目。

## 风格与强度自检

以下是作者辅助的主观编辑自评，未校准，不是论文录用分或科学有效性分数。

| anti-ai-writing 维度 | 自评 / 10 | 依据与限制 |
|---|---:|---|
| Citation integrity | 9 | 当前使用的主要引用与官方记录匹配；不是完整综述 |
| Epistemic accuracy | 8 | 探索性、宽区间与条件差异明确；仍需作者确认整体贡献定位 |
| Specificity | 9 | 单位、分母、协议、门槛和缺失/格式状态有交代 |
| Directness | 8 | 直接叙述观测及限制；四页版仍需压缩 |
| Density | 8 | 方法细节可复核；附录与讨论存在可缩写空间 |

42/50 仅用于本轮编辑排查，不替代同行评审。稿件不使用 em dash，不将零附近/跨零区间写成无效或等效，不将 gate 失败写成方法族失败，不以理论边界、新算法或内部机制作为已建立贡献。

## 窄范围只读核验

按 program.md 写作里程碑要求，由只读子代理 `/root/revision_check` 核验初稿与来源，未发现阻塞性或重大事实/方法错误。其核对涵盖公式、主对照与 AUROC 区分、抽样单位、原 17 项导出记录/6 来源/6 表及两模型原始记录。随后仅补入数据集 provenance 条目和附录表；主结果未变，根会话完成相应来源核验，最终导出为 18/7/7。

这是角色分离的窄范围核验，不是新的正式五席 reviewer-skill 复审、独立人类意见或录用保证。还需作者阅读、模板排版及对最终稿的复核。

最终导出校验还在临时副本中注入一处表格数字改动和一处来源改动，`--check` 均能检出；正确副本通过。原实验文件、审稿快照和历史前缀不变。该测试验证报告同步机制，不证明正文全部论点。
