contract_role: perspective
## Dimension Scores

### D1: methodology_rigor
score: not_assessed

### D2: domain_accuracy
score: not_assessed

### D3: argumentative_coherence
score: not_assessed

### D4: cross_disciplinary_relevance
score: warn
trigger: "主要跨领域含义可以辨认，但局部定义、情境说明或用途边界交代不足，可通过有限澄清或补充解释修复。"

### D5: writing_and_structure
score: not_assessed

### D6: venue_fit_and_contribution
score: not_assessed

## Review Body

本评议对象是研究材料、冻结实验和拟议结论，不能按一篇已完成的论文要求最终叙事。当前材料已经形成系统研究者可理解的实证问题：工具返回处的统计异常、模型是否采取核验行动，以及后续是否获得正确答案，是不同的评价对象。最新 F10–F12 明确限制了机制解释、上下文收益和泛化范围。D4 的主要不足是若干旧的概括仍以“当前中心结论”出现，以及原始记录和运行成本的边界尚未完全连成可直接使用的应用说明。这些问题可通过证据归档和有限的结论整理修复；我没有把未完成的未来系统当成已测试结果，也不对具体发表场景作适配判断。

核对范围包括完整分段阅读本席输入、只读检查 p4_run.py、p4_common.py、context_pilot.py、audit_gemini_recovery.py 及有关数据目录和配置，并运行既有恢复轨迹重计脚本。没有重新执行 bootstrap、重新采集模型回答或联网核验文献。以下观察只用于 D4；其他维度保持未评估。

### S1: 实际可见证据已成为明确且可审计的比较边界

**Evidence Anchor**: text: findings.md，F5/F6/F7 correction，第1项，“rows and min/max are reconstructed from the preview events preceding the scored event”

将 tier 上限与事件发生前实际已展示的行数分开，是系统研究的重要优点。4B 不调用 preview 时不再让核验器凭空获得五行；0 行对应行方法缺失评分，并同时提供 coverage 和 paired-task 支持集。这使“相同上下文”的比较有了可复查含义。代码 exposure_before 也明确只读取此前 preview，并以 head 前缀的最大行数累计暴露量。

### S2: 一次污染与后续真实工具调用的关系有明确披露

**Evidence Anchor**: text: PREREGISTRATION.md，Amendment A-P3b，Threat model，“under `poison_once` it wins outright”

材料承认具有全表重查权限的核验器处于更强的信息条件，并把局部证据核验与再次调用工具区分开。固定返回 pilot 明确禁止重查、允许弃答，P4 则保留自由工具调用，因此两个实验测量的系统行为不同。persistent corruption、权限限制或成本是局部证据设定的应用动机；现有 poison_once 结果没有测量这些环境中的恢复能力。

### S3: 格式失败与判断失败得到分别报告

**Evidence Anchor**: text: findings.md，F10，“The main contrast includes format-related changes, not just semantic judgments.”

pilot 保留 invalid、reject、uncertain、answer=null 和错误数值采用等不同结果，没有将格式失败悄悄重跑或直接称为语义识错。Gemini 的五条无效输出和完整配对敏感性分析，以及 Qwen confidence 含义的后续纠正，有助于相邻领域读者识别接口行为对结果的影响。H5 对仅 7/73 个 subtle paired scalar 任务的结果明确不作全任务结论，同样是必要的边界。

### S4: 统计标错与正确性保证分开，且报告实际误报和漏报

**Evidence Anchor**: table: docs/CONTEXT_EVIDENCE_RESAMPLING_2026-11-07.md，主结果表及“每个原查询的抽样敏感性”表

重复抽样阶段同时给出 161/240 错值标出、14/240 正确值误标和 79/240 错值仍相容，并展示逐查询 2/20、3/20 等低检出情形；没有只用 AUROC 掩盖失败任务。材料说明通过 sanity 不等于校准，compatible 不等于正确，也没有把统计抽样稳健性称为新模型行为复现。对实际工作流而言，这些计数比单个平均 AUROC 更有解释力。

### S5: 已记录的采集完整性可进行独立核对

**Evidence Anchor**: dataset: data/ours/p4/gemini-3.8-flash/T1/audit.json，rows、missing_task_replicates、duplicate_task_replicates、tool_step_alignment_mismatches 和 trajectory_sha256

Gemini 的 630 轨迹、无缺失重复 task/replicate、step alignment 核对和原始轨迹哈希提供了具体审计入口。P4 正规化被逐事件记录；这比把兼容性处理隐藏在运行器内部更有利于解释复现条件。该优点不等于所有实验的原始材料均已齐备。

### W1: 当前中心结论仍保留过强的可达上界措辞

**Severity**: Minor
**Evidence Anchor**: text: findings.md，Central claim, reconciled，“the part no context-limited checker can recover”
**Confidence**: 5 — 可直接比较当前中心结论与同文件限定说明。

F4''' 已说明 0o* 只针对“观测统计量加精确抽样规律”的受限构造，且使用可见样本 spread 的 0r_log 可以在较大 k 超过它；F11–F12 进一步说明不能用信息不足概括所有失败。然而仍以当前中心结论呈现的句子把 0o−0o* 泛称为任何 context-limited checker 均不可恢复的部分，另有 achievable reference 的表述。对系统读者，这会把一个使用全表离线抽样规律的参考构造误读为可部署核验器的普遍信息上界。

建议把这段和 README 的总括统一到最新范围：分别说明已测核验器、受限 oracle 参考、随机行与 head 行，以及选定 matched20 中已展示的统计可提取性。保留历史版本但给出一段唯一的当前结论即可；不要求新增实验或证明普遍上界。

### W2: Qwen 固定返回试验的原始回复尚不能独立审计

**Severity**: Minor
**Evidence Anchor**: absence: data/ours/context_pilot/20261107/qwen3-8b/ — expected 72条原始回复及关联运行信息; checked 目录完整文件清单、scored_responses.json与config.json的存在情况、findings.md的F10 addendum clarification
**Confidence**: 5 — 只读文件清单与作者明确披露相互印证。

该目录实际只有 summary.json、scored_responses.json 和 config.json。现有汇总足以复算保存的计数，但不能从原始回复独立确认 72/72 strict-schema valid、理由内容或评分解析。材料已诚实承认这一缺口，因此这里不将其解释为结果造假，也不否定可复算的 scored-level 对照。它限制的是 Qwen 原始行为与格式审计的证据层级。

最小修复是归档已生成的回复、版本及与 manifest 的对应关系，随后用既定解析器复算并记录一致性；无需重跑模型。若原始记录无法取回，应继续明确将 Qwen 部分标成仅汇总与评分记录可核验，并限制理由和格式结论。核心的选定样本统计可提取性仍有独立的统计实验支持。

### W3: 恢复与错误重试的摘要还缺少时间顺序

**Severity**: Minor
**Evidence Anchor**: dataset: data/ours/p4/gemini-3.8-flash/T1/toxic_seed0.jsonl，SHA256 bd160cc5c29afc0654d27394235161cfebf8f713da9884311ec76e9f13d0d757，既有audit_gemini_recovery.py的恢复轨迹时序重计
**Confidence**: 5 — 直接对已保存轨迹执行既有只读重计脚本。

F9 报告 50 次恢复中 37 次在污染后也出现 Python 错误，但“后来有错误”不能解释核验如何开始。实际重计为：23 次首次后续 Python 调用成功，27 次首次后续 Python 调用出错；10 次是在一次成功 Python 调用后才出现后续错误。因而，不能从 37/50 推断全部恢复主要由错误重试触发，也不能从 23 次成功调用推断其一定属于有意识错。材料已明确 intentional detection 未经单独标注，这一点应保留。

建议在 F9 的恢复摘要加入这些时间顺序计数，并分别标明触发行为、重新执行、得到真值和最终回答恢复。若希望提出主动核验率，应对冻结轨迹预先规定语义标注规则并独立复核；在此之前只报告观测到的后续取证与恢复即可。无须为这一文字修复新增模型调用。

### W4: 离线标错尚未连接到完整的运行时动作与成本

**Severity**: Minor
**Evidence Anchor**: absence: PREREGISTRATION.md的A-CTX-EVIDENCE Operational decisions及A-CTX-RESAMPLE、F9–F12和所附两份统计报告 — expected 标错后的动作规则与对应端到端延迟、额外调用和净错误成本对照; checked 固定flag阈值、误报漏报表、弃答定义、采集usage说明及后续研究计划
**Confidence**: 4 — 系统工作流评估能力范围内，未测量部署环境。

固定阈值已有 flag/compatible 的定义，下一步系统可能选择阻止、弃答、请求新证据或再次运行工具，但这些动作各自的净收益尚未被测量。14/240 clean flags 代表潜在工作流中断，79/240 漏标意味着不能把 compatible 当成授权信号。B=2000 的离线核验、影子置信度调用和重新取证也不是无成本操作。已保存 usage 的美元估计不涵盖未知内部 HTTP 重试尝试，运行器确实采用有界重试而没有逐尝试遥测。

当前结果足以讨论研究可行性，无须为了这份材料立即实现部署系统。最小修复是增加一张权限与动作说明表：在 poison_once 可重查、禁止重查、持续污染等条件下，哪些动作只是建议，哪些已有行为证据；并将现有开销标为离线或保存响应的测量。若后续主张可部署收益，则需按预定策略测量错误最终答案、误阻断、弃答、恢复、延迟和调用成本，避免把未来架构或统计判别率当作已经验证的端到端收益。

总体而言，这批材料支持一项范围明确的系统实证研究：在已测数值返回协议下，局部证据、证据处理方式、接口格式和重查机会都影响可解释的核验结果。其应用意义目前是指导核验边界与后续干预设计。当前材料尚未建立持久污染下的恢复、通用工具返回覆盖或部署收益；作者最新报告已大体承认这些边界，以上修复旨在使各入口的当前结论一致。

