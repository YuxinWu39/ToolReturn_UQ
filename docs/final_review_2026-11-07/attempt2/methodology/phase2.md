contract_role: methodology
## Dimension Scores

### D1: methodology_rigor
score: block
trigger: "通过现有原始材料的重分析、补充披露或明确缩小估计对象仍有可行修复路径"
block_class: repairable

### D2: domain_accuracy
score: not_assessed

### D3: argumentative_coherence
score: block
trigger: "主结论包含现有分析未建立的关键推断"
block_class: repairable

### D4: cross_disciplinary_relevance
score: not_assessed

### D5: writing_and_structure
score: not_assessed

### D6: venue_fit_and_contribution
score: not_assessed

## Review Body

本报告审查的是研究材料及拟议结论，未将其当作已成稿论文。最新 F11/F12 的有限描述性结论有可复核支撑；主要阻碍是早期仍被引用的中心论断、决策定义和比较程序尚未与最新证据统一。所列问题均有基于既有材料的修复路径，没有识别出使全部核心实证证据不可挽救的缺陷。本次未执行新模型调用、bootstrap 重测或新增实验，也不作投稿场所适配判断。

### S1: 主要离线结果可以从事件级数据独立复算
**Evidence Anchor**: dataset: data/ours/context_evidence/20261107/events.json 与 data/ours/context_evidence_resample/20261107/events.json，matched20、0d、clean/corrupted 事件。

我直接对每张表的正负分数逐对比较，以严格大于计一分、相等计半分，再按表等权平均。F11 的 0d 为 0.9166666667，标错污染/正确值为 10/12、1/12；F12 为 0.8184375，计数为 161/240、14/240。0a 的相应 AUROC 为 0.5833333333、0.6145833333，也与报告吻合。这核实了保存分数的排序及计数，没有独立核实每份 bootstrap 区间或其抽样覆盖率；这些 AUROC/比例复算不属于文末四类 bounded procedure。

### S2: 后续抽样研究正确保持查询与表的层级
**Evidence Anchor**: text: PREREGISTRATION.md，A-CTX-RESAMPLE Design，“240 query/draw units from six source tables, not 240 independent queries or tables.”

协议将 20 次新行抽样定义为固定十二查询下的重复抽样，没有把 240 个单位当成新增独立任务；保存原试验并明确新旧 AUROC 估计对象不同，也没有将旧模型回复挪用为新行上的回复。六表百分位区间被限定为描述性，严重度与查询绑定的问题被直接披露。这些约束使 F12 对选定查询抽样稳定性的结论基本可解释。

### S3: 近期实验明确区分统计兼容、模型判断与格式失败
**Evidence Anchor**: text: findings.md，F11，“These are prompted model judgments versus a structured-query statistical procedure, not equivalent representations, computation, cost, or calibrated probabilities.”

F10/F11 保留无效输出、弃答、正确值误报及污染漏报，未把拒绝自动当作恢复正确答案。F11 对未过 sanity 的条件隐去真实 AUROC 与跨 context 对比，而 F12 不把观察误报率变成校准保证。对 same-evidence 的解释也承认结构化规格、计算和成本不同；这支持一个有限的可行性观察，而不支持内部机制归因。

### W1: 0o* 的得分差仍被解释为信息上界与不可恢复知识
**Severity**: Major
**Evidence Anchor**: text: findings.md，Central claim, reconciled，“what bounds detection is the information in the observation context”；同段，“the part no context-limited checker can recover”。
**Confidence**: 5 — 统计判别与基准构造的直接方法学判断。

0o* 使用抽样误差的中位数与 IQR 形成绝对距离，并非针对 clean/corrupted 两个分布的最优似然比排序；给它额外的全表采样分布知识，也不能自动使其特定得分成为任何方法的 AUROC 上界。即使限定只使用同一个模板统计量，也需要最优性论证，不能从一个 oracle 启发式的点估计得到“achievable ceiling”。0o 与 0o* 的 AUROC 差同样只是两种打分程序的差，不能识别所有 context-limited 方法不可恢复的信息量。材料后文已承认全行 checker 不受该界约束，F11 更明确禁止通用信息论上界，但中心句和 research-state 的 ceiling 分解尚未同步。最小修复是把二者统一命名为有额外知识的参考程序，将 0o*−0d 和 0o−0o* 报为限定支持集上的经验 AUROC 差；保留随 k 上升和估计器存在差异的观察。若坚持理论上界，需要明确决策类及分布假设并证明最优性，这属于更高成本的另一个论证任务。

### W2: H1 的主切片和决策规则没有唯一的版本账
**Severity**: Major
**Evidence Anchor**: text: PREREGISTRATION.md，A-P4，“H1 = token entropy (1) and verbalized (3) separately, subtle bin, T1”；A-P4b，“H1 statistic unchanged”。
**Confidence**: 5 — 预定估计对象与实际评分脚本可直接比对。

A-P4 指定 subtle，A-P4b 却在声称规则不变时写成 plausible+subtle；research-state 还保留 subtle 与 AUPRC 门槛，而 F6/F7 的 H1 判决和 p4_score_intrinsic.py 第 58、66–68 行使用 P+S 的 AUROC 上端点。这些不是相同的检验对象。A-P4b 在后续 8B 采集前写入，因此不能仅凭此认定其为事后挑选；但 Qwen3-4B 的已见数据、后来预锁定的 8B 测试和原 subtle 命题必须分别报告。最低修复是制作按模型/采集时间的规则表，明确哪次改动替代了哪条主切片及 AUPRC 规则，并以既有分数补齐原 subtle 的同任务、表内估计与区间。未完成前，8B 的 P+S 结论只支持其实际锁定的命题，不能回填为全部原 H1 已确认；无须为此新增模型运行。

### W3: 学习 scorer 的相对比较缺少预定共同支持集差值
**Severity**: Major
**Evidence Anchor**: absence: findings.md F8 及 experiments/scorer/score_scorer.py 的结果输出 — expected A-P3d/P5 指定的共同支持集上 AUROC_7−max(AUROC_0d,AUROC_0r_log) 及配对表级区间; checked 完整 Phase2 材料中的 F8、2026-11-07 更正表、P5 和 score_scorer.py 全部比较输出。
**Confidence**: 5 — 配对性能比较及缺失支持集审查。

F8 以分别计算的 scorer AUROC 和其他信号点估计断言没有超过 baseline，但 0r_log、0d、实际 preview 和 scorer 的覆盖对象不同。2026-11-07 更正也已表明限制到真实暴露事件会改变任务构成。锁定的比较需要同任务、同标签和各方法均可评分的交集，并将不同支持集分别标明；现有 scorer 脚本没有加载 baseline 做该差值。最低修复是仅重分析已保存分数，报告交集任务/表数和表级配对差值区间，或把结论收缩为“该 scorer 未通过自身 sanity/覆盖门槛，未建立预定增益”，不声称完成了相对性能检验。不能把未建立收益写成等效，也不应以失败仪器证明 learned signals 一般无效。

### W4: scorer 的常数表处理仍保留已披露的旧错误
**Severity**: Minor
**Evidence Anchor**: text: experiments/scorer/score_scorer.py，auc 局部函数，“h[c].nunique() < 2”；findings.md，2026-11-07 correction，“Constant scores dropped instead of scored 0.5.”
**Confidence**: 5 — 代码条件与已明确的评分语义直接对应。

P4 helper 已修正为双类常数分数计 0.5，但 P5 的独立 auc 函数仍在分数种类少于二时返回 None，并从表内平均删除该表。对于 epistemic 或其他大量相等得分，这会改变估计对象；当前没有证据证明某个已报告 surprise 数字因此改变，故不把潜在影响扩大为已证实的数值错误。修复该函数并用保存的 scorer 分数核对受影响表数、AUROC 与区间，足以解决；无需重新训练或预测。其自身 sanity 失败的结论并不因此自动消失。

### W5: Qwen 固定返回 pilot 的原始回复缺档限制主要行为对照审计
**Severity**: Major
**Evidence Anchor**: text: findings.md，F10 addendum clarification，“Qwen 0/72 raw replies present in this repository.”
**Confidence**: 5 — 原始测量与派生评分可追溯性的审计判断。

Qwen 的 72/72 schema-valid、决策与置信度解释以及与程序 checker 的行为差距，目前只能从 scored/config 层接受。事件数和摘要内部一致不能独立验证解析器是否正确处理了原回复、截断、理由或采集版本。该缺口已如实披露，不能据此推断造假或把所有统计证据判为无效；它仍使关键模型对照的测量审计不完整。最低修复是归档既有 72 条原始响应和运行版本，再按冻结严格解析器重解析并核对派生计数；若无法找回，则将该模型比较明确降为未完成原始审计的辅助结果，以可审计的 Gemini 和离线统计观察承载主要结论。不要重新生成回复来冒充原记录。

### W6: 当前入口摘要仍把限定的低表现写成普遍不可分
**Severity**: Minor
**Evidence Anchor**: text: README.md，Reading，“nothing tested separates poisoned from clean returns”；findings.md，2026-11-07 correction，“0d and 0a <= 0.56 everywhere”。
**Confidence**: 5 — 当前摘要与同包更正表的直接一致性核查。

更正表本身给出 4B T0_agent 的 0a=0.579、0d=0.562，另有 0o*=0.611–0.616；因此“0a/0d everywhere ≤0.56”也并非与该表一致。总体近随机的日常概括不等于 AUROC=0.5，更不等于未检出即可证明无信息；失败 sanity 的 scorer 和未建立 H1 的切片也应各自注明。最低修复是让 README 只引用更正后的实际暴露/协议两套结果与覆盖，写成“所测信号表现有限，尚未建立预定效果”，并将 F11/F12 的选定 matched20 可用信号作为不同协议下的发现。最新报告已充分限定其推断，所以这里按入口表达与数字同步问题处理，不额外制造一次核心证据否定。

就近期的核心可行性结果而言，十二查询、六表与公共数据先验限制了外推；这些限制已经明确，不能再当成作者声称拥有新表泛化或识别内部机制的证据。最低完成路径是归档和既有数据重分析、清理决策版本、统一中心结论；新表和表示干预属于更强的未来验证，不是修复所有问题都必须先追加的新实验。

## Arithmetic Receipts

### AR1
procedure_id: grim
evidence_anchor: table: docs/CONTEXT_PILOT_2026-11-07_gemini.md，Context 的平均 confidence 表，head5 正确单元格；同模型 summary.json cells 的 valid 字段。
reported_inputs: M=98.5; N=12 个有效回复; confidence 为 0..100 整数; 报告一位小数。
assumptions: context_pilot.py 严格整数校验并对有效 confidence 作未加权均值；report_context_pilot.py 用 .1f 显示；舍入边界不影响本项内部可达值判断。
derivation: 平均数可为 S/12，S 为 0..1200 整数；取 S=1182，得到 1182/12=98.500000000000，位于显示均值的舍入区间内部。
derived_value_or_range: 可达均值 1182/12，四舍五入显示 98.5。
comparison_rule: 检查是否存在整数总分的均值落在显示至一位小数的舍入区间；内部见证值不依赖端点取舍。
status: consistent
rounding_interval: (98.45, 98.55)，按一位小数 nearest/ties-to-even 的实数舍入区间；可达见证不在边界。
nearest_achievable: 1181/12 < 1182/12 = 98.5 < 1183/12；中间值可精确达到

### AR2
procedure_id: grim
evidence_anchor: table: docs/CONTEXT_PILOT_2026-11-07_gemini.md，Context 的平均 confidence 表，head5 错误单元格；同模型 summary.json cells 的 valid 字段。
reported_inputs: M=96.1; N=11 个有效回复; confidence 为 0..100 整数; 报告一位小数。
assumptions: context_pilot.py 严格整数校验并对有效 confidence 作未加权均值；report_context_pilot.py 用 .1f 显示；舍入边界不影响本项内部可达值判断。
derivation: 平均数可为 S/11，S 为 0..1100 整数；取 S=1057，得到 1057/11=96.090909090909，位于显示均值的舍入区间内部。
derived_value_or_range: 可达均值 1057/11，四舍五入显示 96.1。
comparison_rule: 检查是否存在整数总分的均值落在显示至一位小数的舍入区间；内部见证值不依赖端点取舍。
status: consistent
rounding_interval: (96.05, 96.15)，按一位小数 nearest/ties-to-even 的实数舍入区间；可达见证不在边界。
nearest_achievable: 1057/11 < 96.1 < 1058/11

### AR3
procedure_id: grim
evidence_anchor: table: docs/CONTEXT_PILOT_2026-11-07_gemini.md，Context 的平均 confidence 表，random20 正确单元格；同模型 summary.json cells 的 valid 字段。
reported_inputs: M=98.9; N=12 个有效回复; confidence 为 0..100 整数; 报告一位小数。
assumptions: context_pilot.py 严格整数校验并对有效 confidence 作未加权均值；report_context_pilot.py 用 .1f 显示；舍入边界不影响本项内部可达值判断。
derivation: 平均数可为 S/12，S 为 0..1200 整数；取 S=1187，得到 1187/12=98.916666666667，位于显示均值的舍入区间内部。
derived_value_or_range: 可达均值 1187/12，四舍五入显示 98.9。
comparison_rule: 检查是否存在整数总分的均值落在显示至一位小数的舍入区间；内部见证值不依赖端点取舍。
status: consistent
rounding_interval: (98.85, 98.95)，按一位小数 nearest/ties-to-even 的实数舍入区间；可达见证不在边界。
nearest_achievable: 1186/12 < 98.9 < 1187/12

### AR4
procedure_id: grim
evidence_anchor: table: docs/CONTEXT_PILOT_2026-11-07_gemini.md，Context 的平均 confidence 表，random20 错误单元格；同模型 summary.json cells 的 valid 字段。
reported_inputs: M=92.1; N=11 个有效回复; confidence 为 0..100 整数; 报告一位小数。
assumptions: context_pilot.py 严格整数校验并对有效 confidence 作未加权均值；report_context_pilot.py 用 .1f 显示；舍入边界不影响本项内部可达值判断。
derivation: 平均数可为 S/11，S 为 0..1100 整数；取 S=1013，得到 1013/11=92.090909090909，位于显示均值的舍入区间内部。
derived_value_or_range: 可达均值 1013/11，四舍五入显示 92.1。
comparison_rule: 检查是否存在整数总分的均值落在显示至一位小数的舍入区间；内部见证值不依赖端点取舍。
status: consistent
rounding_interval: (92.05, 92.15)，按一位小数 nearest/ties-to-even 的实数舍入区间；可达见证不在边界。
nearest_achievable: 1013/11 < 92.1 < 1014/11

### AR5
procedure_id: grim
evidence_anchor: table: docs/CONTEXT_PILOT_2026-11-07_gemini.md，Context 的平均 confidence 表，matched20 正确单元格；同模型 summary.json cells 的 valid 字段。
reported_inputs: M=98.6; N=11 个有效回复; confidence 为 0..100 整数; 报告一位小数。
assumptions: context_pilot.py 严格整数校验并对有效 confidence 作未加权均值；report_context_pilot.py 用 .1f 显示；舍入边界不影响本项内部可达值判断。
derivation: 平均数可为 S/11，S 为 0..1100 整数；取 S=1085，得到 1085/11=98.636363636364，位于显示均值的舍入区间内部。
derived_value_or_range: 可达均值 1085/11，四舍五入显示 98.6。
comparison_rule: 检查是否存在整数总分的均值落在显示至一位小数的舍入区间；内部见证值不依赖端点取舍。
status: consistent
rounding_interval: [98.55, 98.65]，按一位小数 nearest/ties-to-even 的实数舍入区间；可达见证不在边界。
nearest_achievable: 1084/11 < 98.6 < 1085/11

### AR6
procedure_id: grim
evidence_anchor: table: docs/CONTEXT_PILOT_2026-11-07_gemini.md，Context 的平均 confidence 表，matched20 错误单元格；同模型 summary.json cells 的 valid 字段。
reported_inputs: M=97.0; N=10 个有效回复; confidence 为 0..100 整数; 报告一位小数。
assumptions: context_pilot.py 严格整数校验并对有效 confidence 作未加权均值；report_context_pilot.py 用 .1f 显示；舍入边界不影响本项内部可达值判断。
derivation: 平均数可为 S/10，S 为 0..1000 整数；取 S=970，得到 970/10=97.000000000000，位于显示均值的舍入区间内部。
derived_value_or_range: 可达均值 970/10，四舍五入显示 97.0。
comparison_rule: 检查是否存在整数总分的均值落在显示至一位小数的舍入区间；内部见证值不依赖端点取舍。
status: consistent
rounding_interval: [96.95, 97.05]，按一位小数 nearest/ties-to-even 的实数舍入区间；可达见证不在边界。
nearest_achievable: 969/10 < 970/10 = 97.0 < 971/10；中间值可精确达到

### AR7
procedure_id: grim
evidence_anchor: text: findings.md，F6 clean 的 verbalized confidence 描述，"77.7"。
reported_inputs: M=77.7; confidence 请求 0..100 整数; 一位小数; 旧版本该均值的有效 confidence 项目级 N 未唯一报告。
assumptions: 不将该段的所有 scalar event 数自动替代排除缺失及对齐失败后的有效 confidence N；不将修复后样本追认为修复前样本。
derivation: 离散均值的可达集合为整数总分 S/N；旧均值的实际有效 N 未确定，无法构造唯一可达格点或完成舍入区间核对。
derived_value_or_range: 无可审核的唯一可达格点集合。
comparison_rule: GRIM 必须同时具有整数粒度、该项有效 N 和显示精度；缺 N 不判一致或不一致。
status: not_computable
not_computable_reason: analytic_n_ambiguous

### AR8
procedure_id: grim
evidence_anchor: text: findings.md，F6 poisoned 的 verbalized confidence 描述，"76.7"。
reported_inputs: M=76.7; confidence 请求 0..100 整数; 一位小数; 旧版本该均值的有效 confidence 项目级 N 未唯一报告。
assumptions: 不将该段的所有 scalar event 数自动替代排除缺失及对齐失败后的有效 confidence N；不将修复后样本追认为修复前样本。
derivation: 离散均值的可达集合为整数总分 S/N；旧均值的实际有效 N 未确定，无法构造唯一可达格点或完成舍入区间核对。
derived_value_or_range: 无可审核的唯一可达格点集合。
comparison_rule: GRIM 必须同时具有整数粒度、该项有效 N 和显示精度；缺 N 不判一致或不一致。
status: not_computable
not_computable_reason: analytic_n_ambiguous

### AR9
procedure_id: grim
evidence_anchor: text: findings.md，F7 T1 clean 的 verbalized confidence 描述，"92.9"。
reported_inputs: M=92.9; confidence 请求 0..100 整数; 一位小数; 旧版本该均值的有效 confidence 项目级 N 未唯一报告。
assumptions: 不将该段的所有 scalar event 数自动替代排除缺失及对齐失败后的有效 confidence N；不将修复后样本追认为修复前样本。
derivation: 离散均值的可达集合为整数总分 S/N；旧均值的实际有效 N 未确定，无法构造唯一可达格点或完成舍入区间核对。
derived_value_or_range: 无可审核的唯一可达格点集合。
comparison_rule: GRIM 必须同时具有整数粒度、该项有效 N 和显示精度；缺 N 不判一致或不一致。
status: not_computable
not_computable_reason: analytic_n_ambiguous

### AR10
procedure_id: grim
evidence_anchor: text: findings.md，F7 T1 poisoned 的 verbalized confidence 描述，"92.4"。
reported_inputs: M=92.4; confidence 请求 0..100 整数; 一位小数; 旧版本该均值的有效 confidence 项目级 N 未唯一报告。
assumptions: 不将该段的所有 scalar event 数自动替代排除缺失及对齐失败后的有效 confidence N；不将修复后样本追认为修复前样本。
derivation: 离散均值的可达集合为整数总分 S/N；旧均值的实际有效 N 未确定，无法构造唯一可达格点或完成舍入区间核对。
derived_value_or_range: 无可审核的唯一可达格点集合。
comparison_rule: GRIM 必须同时具有整数粒度、该项有效 N 和显示精度；缺 N 不判一致或不一致。
status: not_computable
not_computable_reason: analytic_n_ambiguous

### AR11
procedure_id: grim
evidence_anchor: text: findings.md，F7 T0_agent clean 的 verbalized confidence 描述，"91.5"。
reported_inputs: M=91.5; confidence 请求 0..100 整数; 一位小数; 旧版本该均值的有效 confidence 项目级 N 未唯一报告。
assumptions: 不将该段的所有 scalar event 数自动替代排除缺失及对齐失败后的有效 confidence N；不将修复后样本追认为修复前样本。
derivation: 离散均值的可达集合为整数总分 S/N；旧均值的实际有效 N 未确定，无法构造唯一可达格点或完成舍入区间核对。
derived_value_or_range: 无可审核的唯一可达格点集合。
comparison_rule: GRIM 必须同时具有整数粒度、该项有效 N 和显示精度；缺 N 不判一致或不一致。
status: not_computable
not_computable_reason: analytic_n_ambiguous

### AR12
procedure_id: grim
evidence_anchor: text: findings.md，F7 T0_agent poisoned 的 verbalized confidence 描述，"90.2"。
reported_inputs: M=90.2; confidence 请求 0..100 整数; 一位小数; 旧版本该均值的有效 confidence 项目级 N 未唯一报告。
assumptions: 不将该段的所有 scalar event 数自动替代排除缺失及对齐失败后的有效 confidence N；不将修复后样本追认为修复前样本。
derivation: 离散均值的可达集合为整数总分 S/N；旧均值的实际有效 N 未确定，无法构造唯一可达格点或完成舍入区间核对。
derived_value_or_range: 无可审核的唯一可达格点集合。
comparison_rule: GRIM 必须同时具有整数粒度、该项有效 N 和显示精度；缺 N 不判一致或不一致。
status: not_computable
not_computable_reason: analytic_n_ambiguous

### AR13
procedure_id: p_from_test_statistic
evidence_anchor: text: findings.md，F3' SUPERSEDED 说明，"the hypergeometric test (p ~ 7e-5)"。
reported_inputs: hypergeometric test; p 约 7e-5; 未报告可对应的标准 t/z/F/chi-square 统计量、所需参数或完整超几何列联计数。
assumptions: 不将 exact hypergeometric p 转为 chi-square 近似，不从不同段落的事件/任务样本量拼接缺失的检验输入。
derivation: 此 exact 检验不在以标准统计量和自由度反推 p 的已规定边界内；该段亦无完整参数可复核其自定过程。
derived_value_or_range: 不能按本 bounded procedure 推导该 p。
comparison_rule: 不延伸 p_from_test_statistic 到未提供程序输入的 exact 检验；不据此宣称历史 p 正确或错误。
status: not_computable
not_computable_reason: nonstandard_p_procedure
tail_convention: unstated
