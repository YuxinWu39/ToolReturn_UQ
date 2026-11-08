contract_role: domain
## Dimension Scores

### D1: methodology_rigor
score: not_assessed

### D2: domain_accuracy
score: block
trigger: "机制判断缺少区分竞争解释所需的领域依据"
block_class: repairable

### D3: argumentative_coherence
score: not_assessed

### D4: cross_disciplinary_relevance
score: not_assessed

### D5: writing_and_structure
score: not_assessed

### D6: venue_fit_and_contribution
score: not_assessed

## Review Body

本报告评估研究材料与拟议结论，不把它当作已有完整引言、方法和讨论的定稿。已完整读取本席位输入，并核对 oracle 实现及若干关键文献的官方原文。D2 的可修复阻断主要来自仍被当作当前解释使用的信息上界和分解措辞，以及最近邻工作的实质性误述；并非认定实验数值全部错误，也不以缺少新算法否定实证研究价值。没有正式目标绑定，本报告不判断场馆匹配或录用概率。

### S1: 同样本对照提出了有意义且边界清楚的经验问题

**Evidence Anchor**: text: findings.md，F11 — "These are prompted model judgments versus a structured-query statistical procedure"；"not equivalent representations, computation, cost, or calibrated probabilities."

F11 最值得保留的知识是：这十二个选定查询的一份 matched20 证据中，既有统计程序能够提取判别信号，而模型判断仍接受不少错误值。因此，单纯展示数据不足不能概括这些条件下的全部失败。材料明确区分相同数值证据与相同表示、计算、成本，没有据此确定模型内部机制。这个限定结论有独立的实证价值；它不需要被包装成新算法。

### S2: 行抽样稳健性检查没有被冒充模型差距的重复验证

**Evidence Anchor**: table: docs/CONTEXT_EVIDENCE_RESAMPLING_2026-11-07.md，“结论”主结果表及“每个原查询的抽样敏感性”表。

F12 给出 0d 的 161/240 错误标记和 14/240 正确误标，逐查询结果也显示明显异质性。报告保留原冻结样本与新抽样混合目标的区别，并明确没有在新行上重新测量模型。它支持这些选定查询存在可利用统计信号，未将 240 个 draw 写成 240 个新任务，也未声称模型差距已经跨 draw 复现。

### S3: 最新外部复现对行为与置信度的区分较为准确

**Evidence Anchor**: text: findings.md，F9 — "Recovery is an outcome after further evidence calls."；"Intentional error detection requires separate annotation."

F9 分别报告暴露、采纳、后续证据调用和恢复，并披露 37/50 恢复轨迹在污染后发生过 Python 错误。它没有把 poison_once 下取得后续正确证据等同主动识错。对 7/73 subtle 配对标量任务的 H5 也明确不予确认。这与官方 [Trace-vs-label 原文](https://arxiv.org/abs/2610.30491) 所强调的最终正确、重新核验与错误传播并不等价相吻合。

### W1: 0o* 是特定 oracle 分数，尚不能解释为可达信息上界或纯估计器损失

**Severity**: Major
**Evidence Anchor**: text: findings.md，F4''' — "the achievable ceiling for a k-row checker using the template statistic is ~0.73 at five rows"；Central claim, reconciled — "the part no context-limited checker can recover"
**Confidence**: 5 — 已核对 A-P3d 定义及 zeroparam.py 中 oracle_law、score_0o_star 的实际计算。

0o* 使用全表及真实聚合值生成的任务专属参考量。代码用 M=300 个全表子集估计 b_k 和 w_k，再计算偏差校正后的绝对标准化残差；这里既没有完整精确抽样律，也没有证明该分数对所允许的信息集合具有最优 AUROC。即使只允许使用观测统计量和参考律，非对称、多峰或特定污染分布下，绝对标准化距离也不自动等同最优检验。F4''' 对“完整可见行并非受此上界约束”的补充限制是必要的，但不能补出统计量受限类中的最优性。

此外，0d 从样本估计其参考区间，而 0o* 获得了全表生成的 bias/spread。两者差值同时改变参考知识和打分规则，不能仅凭 AUROC 相差约 0.11 就认定这些都是相同行中本可恢复、只被 bootstrap 浪费的信号；0o−0o* 也不能直接解释成任何 context-limited checker 都无法恢复的那一部分。头五行并非随机抽样时，所用随机行参考律还有额外失配，低分不能确立信息不足机制。

最低修复是将三条曲线称为已测 bootstrap、任务专属 draw-centred oracle reference 和 population-centred reference，明确 M=300 是 Monte Carlo 近似；将两项差值改为方法间的描述性差距，删除不可恢复性和可达上界措辞，并统一 README、当前 central claim、图注和 research-state 中未撤销的解释。这样不必重跑就能保留行数曲线及已有数值。更强方案是明确可观测量、参考知识及污染模型，给出最优性证明或同信息条件下的检验比较，再讨论边界；该方案属于新增理论或分析，不能把预期结果写成已完成结论。此问题实质削弱当前核心机制解释，但不使 F11/F12 的限定经验结果消失，故不定为 Critical。

### W2: 最近邻工作的模型条件被误述，现有定位尚未辨清已有发现与本研究增量

**Severity**: Major
**Evidence Anchor**: text: research-state.yaml，literature.key_papers，2608.22676 条目 — "nearest prior: 2 signals at return boundary, closed model, 1 domain"
**Confidence**: 5 — 已核对最近邻官方 v2 全文的方法定义、模型说明及 ToxicBench 的受控证据实验。

该最近邻的官方原文 II-C 明写使用 Qwen3-8B；因此 closed model 的描述不成立，本研究的 Qwen3-8B 结果也不能被当成相对于它的开放模型覆盖增量。其 II-B 区分返回内容在 schema/full-prefix 下的 surprisal，以及合法动作集合上的 entropy；后者并非本研究对生成 action 所有 token 求平均的 entropy。笼统写两个信号会掩盖比较对象的差异，也不足以支持“已有信号已被系统覆盖”的读法。[Robustness Analysis 原文](https://arxiv.org/html/2608.22676v2)

另一项关键重叠是：ToxicBench 本身已经使用配对 clean/poisoned 条件研究采纳与检查，附录 E.2 还在三张公开表上固定父轨迹并操纵后续证据。因而，污染会被采纳、检查不必然恢复、证据条件影响结果这些方向已有直接前例，不能单独承担本研究的主要新增知识。[ToxicBench 原文 §3–4、附录 E.2](https://arxiv.org/html/2609.37153v1)

最低修复需要围绕主张重写领域定位，而非仅纠正一个模型名称：逐项列出返回边界、参考信息、动作/词元信号定义、数据域、行抽样预算、评价标签及既有结论。可保留并待进一步核实的增量包括：标量数值缩放下的可见行预算曲线、真实 exposure/覆盖率审计、在相同展示样本上比较结构化统计核验与提示判断，以及选定查询的独立行抽样稳定性。这些不是已经证明的“首次”，但足以形成可检验的经验贡献。若最终要声称对最近邻信号做了直接性能比较，还需实际实现其定义或清楚声明未比较；当前没有该实验，不要求以预设结果补齐。

### W3: 零挑战的标题措辞仍比所用行为指标能支持的范围更宽

**Severity**: Minor
**Evidence Anchor**: text: README.md，“Headline results”第一行 — "0 challenges in 3,780 trajectories"
**Confidence**: 4 — 已结合 F5–F9 的指标说明与官方行为测量论文核查概念范围，未逐条人工重标全部 Qwen 轨迹。

最新 F9 已准确区分自动 flag、后续证据调用和意图性检测，README 的 challenges 却没有说明对应哪个可观测事件。anomaly_detection=0 或没有重查不能直接证明从未产生怀疑；poisoned_answer_used 也曾是包含提及的 legacy flag。最低修复是把标题改成所运行检测器的零标记结果，并在同处列出 used/all-toxic 与 used/exposed，说明是否做过人工 trace 核验。若要保留人类行为意义上的“零挑战”，则需要定义挑战并开展相应标注。这是可局部修复的测量措辞问题，不额外要求新模型运行。[Trace-vs-label 官方论文](https://arxiv.org/abs/2610.30491)

### W4: 学习型 scorer 的失败解释仍把一种相容诊断写得过于确定

**Severity**: Minor
**Evidence Anchor**: text: findings.md，F8 — "learns the scale of a column, not the statistic to within 10-50%"
**Confidence**: 4 — 判断基于 F8 的 held-out 预测误差、coverage 与 sanity 结果，未复训或做表示探针。

训练配置在留出表上误差很大、区间覆盖差且 sanity 失败，足以支持这个配置未成为有效污染检测器。预测与真值存在一定相关性，与学习到了粗数量级相容；但现有结果并未区分目标表征、输入截断、训练规模、跨表迁移和模型容量的影响，不能确定它究竟学会了什么内部表示。将这一句改成受观测支持的行为诊断，并把候选原因保留为假说即可。该负结果有价值，但不能作为学习型核验普遍受信息限制的独立证明。

### 领域结论与文献核验范围

可以成立的当前研究主线是：在明确限定的数值污染、信息暴露与核验协议下，分别量化代理行为、信号区分度、覆盖及同样本统计可用性。F11/F12 尤其适合支持“展示证据的可用性与核验程序的利用应分开测量”。对模型机制、新任务泛化、全方法不可能性和最优信息边界则仍应留白。缺少新算法本身不构成本席位的负面发现。

本次核验了 ToxicBench 与 Robustness Analysis 的官方全文，另核验 Loud Failures, Quiet Failures、Trace-vs-label、VoS 和 Don't Blindly Trust It 的官方摘要。Loud/Quiet 对提示检查未改善检测的简写，以及 VoS 对失败轨迹识别与有效干预步骤定位的区分，在其已测范围内与官方摘要相符；这些摘要核验不代表已全面审计全部五十条书目。[Loud/Quiet](https://arxiv.org/abs/2610.10062)、[VoS](https://arxiv.org/abs/2610.09115)、[Don't Blindly Trust It](https://arxiv.org/abs/2606.21409)

上述引用均已存在于所供书目，本报告没有推荐新增文献；未读取其他席位报告，未修改研究材料，也未运行新实验。
