contract_role: da
## Dimension Scores

### D1: methodology_rigor
score: not_assessed

### D2: domain_accuracy
score: not_assessed

### D3: argumentative_coherence
score: block
trigger: "核心推断存在实质证据缺口、未排除的竞争解释或关键概念偷换，使当前结论不能成立，但通过补充有区分力的证据、重建推理或实质收缩结论仍可能修复。"
block_class: repairable

### D4: cross_disciplinary_relevance
score: not_assessed

### D5: writing_and_structure
score: not_assessed

### D6: venue_fit_and_contribution
score: not_assessed

## Review Body

criteria_binding_unavailable

本席审查的是研究材料及拟议结论，不把尚未形成最终论文当作研究结果无效。D3 的 repairable block 针对目前仍并存的两段核心推理：将指定 oracle 分数的表现解释成信息上界，以及让未通过有效性门槛的 learned scorer 加强“各种信号都因信息不足而失效”的总论。两项各自按 Major 报告；合起来要求重写中心论证，而不是补一句局限即可完成。没有发现必须否定全部经验结果的决定性反证，故不列 Critical，也不判 fatal。

最强反方论证其实来自材料最新版本：作者已经把 F11/F12 限定为选定查询上的证据可提取性，并明确否认通用信息论上界与内部机制证明。若最终论文只提出这一经验命题，同时保留 Qwen 默认协议下的高污染采用率、若干已测信号表现有限以及抽样重复后仍存在统计判别信号，则研究能够成立。Evidence Anchor: text: docs/CONTEXT_EVIDENCE_2026-11-07.md §论文结论现在怎么写 “在选定的数值工具返回任务中，核验表现同时取决于展示的证据和采用的核验程序”；Confidence: 5/5，依据是提供材料的明确结论与范围声明。我的挑战不要求放弃这个较窄命题，而是要求把它贯彻到 README、中心结论、图线名称和负结果的解释中。

替代解释的区分应当保持具体。相同数据行上的统计程序与模型差距，可以来自显式查询规格、计算辅助、提示理解、表示或证据使用过程；它不是只有“缺少数据”与“模型不会使用证据”两个选项。这里作者已主动承认比较的表示与计算不等价，因此不另立一项已被解决的缺陷。Evidence Anchor: text: findings.md §F11 “not equivalent representations, computation, cost, or calibrated probabilities”；Confidence: 5/5，依据是实验信息条件与作者明确披露之间的直接对应。最有区分力的后续研究是作者提出的同样本原始行与派生摘要干预；它是扩展结论的可选路径，不是保留当前描述性结果的必需新实验。

有几项不应被当作缺陷。未提出新算法并不消灭实证审计的价值；统计程序本身不新，仍可用来反驳“所有失败都能归于缺少展示数据”的单一解释。F12 保留所有十二个查询并报告任务差异、79/240 个未标错污染值及误报，能够支持有限的抽样稳健性描述。Evidence Anchor: table: docs/CONTEXT_EVIDENCE_RESAMPLING_2026-11-07.md §结论，0d 行（161/240、14/240、AUROC 0.818）；Confidence: 4/5，依据是提供的汇总和明确的估计对象，未独立重跑 bootstrap。也不能用 0.917 与 0.818 的差值宣称最初样本被挑选，因为二者分别针对固定样本和查询/抽样混合目标。材料已经作此区分，我不将它重复计为问题。

预注册、追加修订和保留失败结果有助于审计，但不能替代论证有效性。我的最低修复路径不要求新的模型调用：首先删去未证明的上界及不可恢复分解措辞，将现有曲线作为指定方法、抽样规则和支持集下的经验参考；其次按门槛通过状态分开报告有效检测证据与训练/测量失败。这样保留下来的论文核心，是受限场景的运行时工具返回核验实证，而非检测不可能性定理、所有 UQ 方法的否定或已确认的模型内部机制。以下两项修复均由作者选择具体表达方式；若希望坚持更强的命题，则需要额外理论或验证，而不是本席代拟结果值。

#### CRITICAL

| # | Issue | Evidence Anchor | Confidence | Decision Impact | Minimum Remedy |
|---|---|---|---|---|---|

#### MAJOR

| # | Issue | Evidence Anchor | Confidence | Decision Impact | Minimum Remedy |
|---|---|---|---|---|---|
| M1 | 指定 oracle 的经验 AUROC 尚未构成信息上界，分数差值也未被识别为可恢复与不可恢复的信息分解。0o* 仅以有限次全表抽样估计 bias/IQR，再对观察统计量与候选值使用绝对标准化距离；知道这些量不意味着该排序在污染检测问题上最优。即使只限制使用模板统计量，仍需最优性论证，不能从该分数直接推出 ceiling。材料对更丰富输入的 caveat 是必要修正，但没有证明剩下的受限上界；对非随机 head5 使用随机抽样 law 更不能支撑通用限制。 | text: findings.md §Central claim, reconciled “what bounds detection is the information in the observation context”；PREREGISTRATION.md §A-P3d “not recoverable by any k-row checker”；experiments/zeroparam.py:319–359，oracle_law 与 score_0o_star “return d, abs(d)” | 5/5：直接核对协议、中心表述与 oracle 实现，结论限于缺少所需最优性论证。 | 使目前以信息上限解释各类检测失败的核心推理不能成立，但不否定 0d/0o/0o* 已测经验曲线，也不否定 F11/F12 的信号存在性。单独不足以推翻收窄后的研究，故为 Major。 | 将 exact law 改为有限 Monte Carlo 的 bias/spread 参考，将 ceiling/不可恢复/estimator loss 改为指定分数之间的描述性差异；统一 README、F4'''、central claim 与图注。保留更强上界须另给明确可观测量、候选分布与最优排序的证明；成本明显更高，可由作者选择。 |
| M2 | learned scorer 的失败没有提供一个有效检测器的强否定证据，因而不能增强所有信号在默认 context 下都因信息容量而失效的解释。训练拟合、测试迁移和工具有效性是不同环节；该实例既未覆盖 clean quantile 目标，也未通过极端扰动 sanity。其 AUROC 可作为训练失败诊断保留，但不能同时被头条列作可用检测方法的普遍失败。材料已诚实报告失败，这降低诚信担忧，却没有修复 README/F8 的总括推断。 | text: findings.md §F8 “fails its own sanity and calibration rules”；“the paper's contribution rests on C1”；“with the information-capacity curve explaining why”；README.md §Headline results “Clean-only learned scorer” | 5/5：作者直接报告门槛失败，并在同一节给出总括推论；未独立重训模型。 | 影响负结果可支持的对象范围和原因解释，需要实质重写证据层级，但保留该配置的训练/迁移失败以及合格基线的经验结果。没有证据说全部研究无效，故为 Major。 | 从“有效信号检测表现”头条中移出或明确标为 gate-failed diagnostic；把结论限定为此 backbone、训练数据、目标和配置未得到可用 scorer，不据其推断 learned UQ 的一般无效或信息不足机制。修复现有论证无需新训练；若坚持比较一个有效 learned detector，再先独立证明其 sanity 与 held-out coverage 合格。 |
