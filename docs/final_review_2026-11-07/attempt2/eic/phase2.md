contract_role: eic
## Dimension Scores

### D1: methodology_rigor
score: not_assessed

### D2: domain_accuracy
score: not_assessed

### D3: argumentative_coherence
score: not_assessed

### D4: cross_disciplinary_relevance
score: not_assessed

### D5: writing_and_structure
score: warn
trigger: "核心内容仍可理解和审查，但局部术语解释、段落衔接、图表标注或范围说明不充分，需定点修订以减少歧义。"

### D6: venue_fit_and_contribution
score: block
trigger: "现有材料未充分建立所声称的原创增量或重要性，需要新增关键比较、补充证据或实质收窄贡献陈述后才能评价，但仍存在保留研究核心的修复路径。"
block_class: repairable

## Review Body

本席审查研究产物及拟议结论，未将其视为完成的论文。已完整阅读本轮提交包，并只读核对原始 program.md 及源文件目录；未重跑实验、核算全部指标或联网核验文献。D1—D4 留给指定席位。D6 仅评价领域通用贡献和证据范围：没有正式目标绑定，具体 venue fit 未评，也不提供录用概率。材料中的既往审查标签不构成本席结论。

研究的可辨认核心是在数值工具返回处区分展示证据、核验程序与 agent 行为，并用同证据检查说明部分失败不能仅由展示数据量概括。材料仍可审查，D5 的问题主要是当前摘要与状态索引未完全同步。D6 的可修复阻碍是中心贡献混用受限参考与一般信息界限，且缺少最近工作对照。缺少完整稿不构成单独负面发现，以下问题也不构成研究造假的证据。

### S1: 实验问题具有清楚的范围
**Evidence Anchor**: text: README.md，Scope 段 — "numeric, single-scalar tool returns on tabular data"；"one corruption type (scaling)"

研究对象、污染形式与默认观测边界具体明确。head5、随机 k 行和 matched20 的区别也有记录，可以组织范围限定的实证贡献；此优点不证明跨污染类型泛化。

### S2: 预测失败和负结果得到保留
**Evidence Anchor**: text: findings.md，F8 — "the P5 prediction [0.55, 0.70] is missed"；"C3 as specified in P5 is a **negative result**"

学习器预测落空、校准及 sanity 失败均被披露，H1/H5 未达阈值也在对应结果段保留。特定实现的失败有报告价值，其解释边界见 W3。

### S3: 同证据检查形成了可检验的经验问题
**Evidence Anchor**: text: findings.md，F11 Interpretation — "Insufficient displayed data alone cannot summarize all model failures"；"No new algorithm or universal bound."

相同可见数据上，既有统计程序可以提取信号；材料同时承认结构化规格、表示和计算不同。这支持继续区分证据可用性与证据利用，没有把经验差距直接视为内部机制或新算法优势。

### S4: 抽样复查限定了估计对象和独立单位
**Evidence Anchor**: text: findings.md，F12 — "Single-draw 0.917 and mixture 0.818 estimate different targets"；"No new table/task generalization"

240 个 query/draw 单位仍被说明来自十二查询、六表，未当成新增独立任务，也未把旧模型回答移植到新行。新旧估计、查询异质性和轻微污染漏检均可见。

### S5: 修正记录说明了错误的影响
**Evidence Anchor**: text: findings.md，F5/F6/F7 correction，第 3 项 — "Constant scores dropped instead of scored 0.5."；"Direction of this bug favoured us"

实际曝光、事件对齐与常数分数处理的修正及后果得到保留，允许追溯数字版本。后述摘要和状态索引需要同步，历史记录应继续保留。

### W1: 当前中心主张将受限 oracle 参考扩展为一般信息界限
**Severity**: Major
**Evidence Anchor**: text: findings.md，Central claim, reconciled — "what bounds detection is the information"；F4 最终版 unfiltered mean/median caveat — "Neither is a bound on a checker that reads the query and the full visible rows."
**Confidence**: 5 — 当前中心主张与同文件适用范围限定可直接比对。

标为 reconciled 的主张仍将 0o−0o* 说成任何 context-limited checker 无法恢复的部分，而同文件承认该参考只涉及指定统计量与精确抽样律；使用可见行离散程度的 0r_log 还可在部分条件超过它。全表生成的偏差与尺度知识，也不等于部署时可由可见行取得的知识。随机 k 行曲线可描述这些程序，尚不足以确立任意核验器的最优性能或唯一瓶颈。F11/F12 的较窄解释是积极修复，但尚未替换仍被标为当前中心主张的版本。

最小修复是实质改写中心贡献，限定为有限任务、抽样规则与核验程序的实证比较；将 0o* 标为依赖指定统计量、带特权抽样律知识的参考，清除对任意 checker 的界限及可恢复损失断言。若保留最优上界贡献，需另给允许的核验器、信息集合与最优性依据。已有实证材料可以保留。

### W2: 最终领域增量尚缺近邻工作对照
**Severity**: Major
**Evidence Anchor**: absence: 提交材料的贡献定位 — expected 将最终贡献逐项对照最近工作的研究单位、污染、可见证据操纵、信号及结论范围的明确说明; checked README.md、findings.md 当前贡献段、research-state.yaml 的 literature 与 open_problems、docs/references_verified.bib 及原源 program.md
**Confidence**: 4 — 能检查材料是否建立比较；未联网或阅读所列文献全文。

文献清单及简短相关性说明丰富，但尚未把最终贡献逐项对照最近工作。open_problems 仍偏向系统比较与 failure taxonomy，晚期同证据检查和抽样敏感性尚未形成统一增量论证。问题值得研究并不自动建立原创性；没有新算法也不等于没有贡献。

最小修复是建立由原文支撑的近邻比较表，优先核查 ToxicBench、RobustnessAnalysis、TrajectoryAdaptedUQ 与相关 step-level UQ 研究，明确新增的实证问题、证据与局限。这里只列待核查候选，不断言这些文献实际覆盖什么。每项贡献绑定已有结果及未完成检验，撤回尚未建立的首创性表述。优先需要比较与贡献重写，无须先增加模型运行；没有发现可支持 fatal 的完整重复证据。

### W3: 失败 sanity 的学习器仍进入概括性无效结论
**Severity**: Major
**Evidence Anchor**: text: findings.md，F8 标题与 Paper consequence — "fails its own sanity and calibration rules"；"every signal, learned or not, is at chance under the default observation context"
**Confidence**: 5 — 有效性门槛与贡献推论在同一条目中可比。

该实现连极端污染与 held-out clean coverage 门槛都未通过，可支持此训练配置未形成可用检测器；不足以与有效检测器等量齐观，支持学习信号家族缺乏判别信息或信息不足的解释。README 的 headline AUROC 未就近标注失败 gate，易被当成有效检验后的负结果。部分 H1 上界未达预定阈值，也需区分点估计偏低与确认性结论。

保留 P5 为失败训练／迁移实例，在首页与贡献总结并列 gate 状态，将 C1 限定到已测、有效且具有相应支持集的具体指标。不必为了报告负结果重新训练；只有保留学习信号家族普遍无效的主张，才需要有效实例及额外证据。

### W4: 修正段的数值范围仍未同步
**Severity**: Minor
**Evidence Anchor**: table: findings.md，F5/F6/F7 correction 的 Within-table AUROC before -> after 表，4B T0_agent 行 0a=0.579，与随后 What changes in the text 中关于 0d 与 0a 在所有条件均不超过 0.56 的陈述
**Confidence**: 5 — 同一修正段可直接核对表值与摘要。

表中 0a=0.579 超过文字的 0.56。首页 0.53—0.58 与表较一致，故这是局部范围未同步，没有单独推翻主要结果。请按 actual-exposure／protocol、tier、支持集及 coverage 写确切范围，区别较低 AUROC、接近 0.5 与低于实用阈值；不需新实验。

### W5: 全称归档承诺超过 Qwen pilot 的原始材料覆盖
**Severity**: Minor
**Evidence Anchor**: text: README.md，归档承诺 — "All agent trajectories and scored events are committed"；findings.md，F10 addendum clarification，Audit scope — "Qwen 0/72 raw replies present in this repository."
**Confidence**: 4 — 缺口由提交材料披露；未逐个审计响应目录。

scored/config 可支持计数的有限复核，但原始回答缺失限制格式、理由和提示遵从的独立审计。请在首页按实验列 raw、scored、config 与可重算范围，从既有实例归档 72 条回答及环境；暂不可得则明确仅核验到评分记录。不要重跑替代原回答，也不要把该缺口解释为造假。此项影响审计覆盖，未单独否定已核对的计数。

### W6: 当前假设索引混用旧门槛与更新结果
**Severity**: Minor
**Evidence Anchor**: text: research-state.yaml，H1—H4 状态及 G1 statement — "status: pending"；"PILOT GATE: observation failures >= 15% of all failures in paired runs"
**Confidence**: 5 — 可与 A-P1、F7、F8 更新直接对应。

当前索引仍将 H1—H4 留为 pending，G1 statement 仍保留已退休的 15% 门槛；findings 已按 agent/tier 给出部分 H1 状态、P5 负结果及 H4 按原排名方式不可检验的限制。P5 不等于 H2 已完成，未测项也不应强填成功或失败；索引未分清完成、部分完成、替代及未测，需要读者重建成熟度。

请建立当前状态矩阵，链接假设版本、统计量、agent/tier、支持集及结果，保留旧协议。替代条目标明有效版本，未执行项继续标未执行。完整稿可随后围绕矩阵组织，无须为形式完整补跑原始计划。
