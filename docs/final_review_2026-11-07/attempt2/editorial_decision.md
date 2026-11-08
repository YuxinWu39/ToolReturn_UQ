# 综合审查意见：研究产物与拟议结论

calibration_status: NOT_CALIBRATED

## 判定：Major Revision（大修后再定稿）

这是对 f41db23 研究材料的模拟评估，不是实际场馆裁定。缺少完整论文正文，未判断版式合规、具体 venue fit 或录用概率。最新 F11/F12 的限定事实可保留；尚需修复的是旧中心论证、规则版本与证据审计边界。没有席位认定全部核心实证数据无效，DA 的 CRITICAL 表为空。

dimension_verdicts: [D1=block, D2=block, D3=block, D4=warn, D5=warn, D6=block]
fired_conditions: [F2, F3, F5]
da_critical_adjudications: []
editorial_decision=major_revision

## 判定依据

按合同只计算 eligible roles：D1/D2/D3/D6 为可修复 block，D4/D5 为 warn，未出现 fatal。F2 优先于其余已触发条件，因此大修而非接受或拒绝。不得用平均评分、信心数值或人设数量改写结果。

共同实质问题是 oracle 参考被扩写为信息上界，未通过门槛的 learned scorer 又被用于总括性无效论断。不同席位对此及原始归档缺口的严重度分级存在差异，保留差异，不声称五位一致。

## 仍然成立的发现

- 原冻结相关样本中，0d 标出 10/12 错误、误标 1/12 正确。方法席从保存事件重算 AUROC 0.9166667 与计数一致。
- 对相同十二查询独立抽样后，0d 标出 161/240 错误、误标 14/240 正确，query/draw mixture 表内 AUROC 0.8184375；仍仅六表、十二查询。
- 固定返回模型试验未建立相关20行相对随机20行的跨模型稳定收益。两模型主区间跨零，不是等效或无效证明。
- 统计稳健性阶段没有新模型回答。相同数值样本也不等于相同表示、查询规格、计算和成本，不能识别内部机制。

## 当前阻碍（来自已保存报告）

| 问题 | 来源 | 最小处理 |
|---|---|---|
| 信息上界及不可恢复信息分解未被证明 | EIC W1、R1 W1、R2 W1、R3 W1、DA M1 | 改为具体程序与信息条件下的经验参考，统一唯一当前结论。 |
| 预定统计与比较口径没有闭合 | R1 W2–W4、EIC W3/W6 | 澄清 H1 subtle/P+S 版本；P5补共同支持集比较或撤回该比较主张，并核对常数表处理。 |
| 增量定位与审计范围未统一 | EIC W2/W5、R2 W2/W3、R1 W5、R3 W2/W3 | 纠正近邻工作描述；补既有 Qwen 原始回复或降级为辅助证据；恢复与重试加入时序。 |

以上不是工作排序。完整来源条目和可验证条件按原席位顺序见 revision_roadmap.json；未替作者选择取舍或授权修改正文。保留缩窄后的实证研究，不必为清理这些论证问题先增加模型运行。新表、原始行/统计摘要干预是支持更强机制或泛化的扩展。

## 可供论文采用的保守结论

在已测数值工具返回任务与核验协议下，直接增加查询相关样本尚未建立跨模型稳定的核验收益。对选定查询，已有 bootstrap 程序可从相同展示样本中提取判别信号；独立行抽样后仍观察到信号，但检出与误标随任务及抽样变化，轻微扰动切片仍有大量漏检。因此，应分别评价证据的可用性与核验程序的证据利用。“信息不足”不足以概括全部失败；本研究未建立通用信息上界、未识别模型内部机制，也未证明新算法优势。

这段是综合现有报告给出的保守措辞建议，不代替作者对完整稿的最终采用。若保留更强结论，需要相应理论或新数据，而不能只追加局限句。

## Review Panel Provenance (#540/#740)

Typed artifact: panel_provenance.json；该文件已通过构建与重放校验。五席来自不同 fresh invocation contexts；不据此宣称误差独立。精确模型族、提供者和无法独立观测的同伴可见性保留 unknown。

| 轴 | 状态 |
|---|---|
| blind_to_peer_outputs | unknown |
| fresh_context | true |
| human_distinct | false |
| model_family_distinct | unknown |
| provider_distinct | unknown |
| role_separated | true |

Model-family provenance is incomplete; cross-family separation is unknown, so correlated-error risk cannot be ruled out.

角色报告分别提交；综合由主会话以 editorial_synthesizer 角色执行，不是第六位独立人类审稿人。EIC 与 DA 保存完整报告后收尾回执遇到用量限制；两份保存产物通过同一 conformance 校验，未替换或重新生成审稿内容。

## 修改清单（源顺序，不是优先级）

- REV-EIC-W1 [must_fix; major; EIC]: 将 oracle 曲线与差值改为指定方法间的经验参考，统一中心结论并删除未经证明的通用信息上界与不可恢复性措辞。
- REV-EIC-W2 [must_fix; major; EIC]: 以原文建立最近邻比较表，明确研究新增的经验问题，撤回尚未建立的首创性与机制主张。
- REV-EIC-W3 [must_fix; major; EIC]: 按 sanity 与校准状态分层报告，将 learned scorer 定位为该训练配置未形成可用检测器，避免家族普遍无效推论。
- REV-EIC-W4 [should_fix; minor; EIC]: 按实际暴露、协议条件和支持集核对当前摘要数值范围，区分低判别表现与严格无信息结论。
- REV-EIC-W5 [should_fix; minor; EIC]: 从既有记录补齐 Qwen 原始回复与版本；无法取回则明确仅 scored/config 层可核验并收缩行为主张。
- REV-EIC-W6 [should_fix; minor; EIC]: 建立假设版本、统计量、模型/tier、支持集与完成状态矩阵，保留旧协议并明确替代关系。
- REV-R1-W1 [must_fix; major; R1]: 将 oracle 参考与两项经验差值的解释限定到实际得分和信息条件，不保留未证明的最优性/信息分解。
- REV-R1-W2 [must_fix; major; R1]: 按模型采集时间列出 subtle/P+S 与 AUPRC/AUROC 规则版本；重分析既有分数补齐原 subtle 命题，避免回填确认性结论。
- REV-R1-W3 [must_fix; major; R1]: 补齐预定共同支持集的配对比较，或将 P5 收缩为未过自身门槛、未建立增益，不声称已完成相对性能检验。
- REV-R1-W4 [should_fix; minor; R1]: 统一 scorer 对双类常数分数的 0.5 语义，并用既有分数核对受影响表数和估计值。
- REV-R1-W5 [must_fix; major; R1]: 归档既有 Qwen 原始回复与运行版本并按冻结解析器复核；无法取回则降为原始审计未完成的辅助结果，不重新生成替代。
- REV-R1-W6 [should_fix; minor; R1]: 统一入口摘要与更正表的具体范围、覆盖和门槛状态，避免将近随机表现写成所有方法不可分。
- REV-R2-W1 [must_fix; major; R2]: 用任务专属、Monte Carlo 的 oracle reference 描述曲线，将差值解释为程序间经验差异并统一所有入口。
- REV-R2-W2 [must_fix; major; R2]: 纠正最近邻工作实际模型与信号定义，按证据访问、抽样轴和研究单位建立原文支撑的增量对照。
- REV-R2-W3 [should_fix; minor; R2]: 将零挑战改成所用行为检测器的零标记结果，明确分母与人工标注状态。
- REV-R2-W4 [should_fix; minor; R2]: 将 learned scorer 的内部表示解释改成受误差/覆盖观测支持的行为诊断，保留其他失败原因作为候选。
- REV-R3-W1 [should_fix; minor; R3]: 将当前中心结论统一到已测核验器、受限参考、抽样规则与选定 matched20 样本，不保留一般信息界限。
- REV-R3-W2 [should_fix; minor; R3]: 补齐既有 Qwen 原始回复及版本或保留仅评分层可核验的限制，避免扩写理由/格式主张。
- REV-R3-W3 [should_fix; minor; R3]: 在恢复摘要中报告首次后续成功/错误和先成功后错误的时序计数，分开触发、重查、得到真值和恢复。
- REV-R3-W4 [should_fix; minor; R3]: 补充权限与动作边界说明，将离线计算、保存 usage 和未测部署收益分开；若主张端到端收益再另行测量。
- REV-DA-M1 [must_fix; major; DA]: 将 exact law 改为有限 Monte Carlo 的 bias/spread 参考，将 ceiling/不可恢复/estimator loss 改为指定分数之间的描述性差异；统一 README、F4'''、central claim 与图注。保留更强上界须另给明确可观测量、候选分布与最优排序的证明；成本明显更高，可由作者选择。
- REV-DA-M2 [must_fix; major; DA]: 从“有效信号检测表现”头条中移出或明确标为 gate-failed diagnostic；把结论限定为此 backbone、训练数据、目标和配置未得到可用 scorer，不据其推断 learned UQ 的一般无效或信息不足机制。修复现有论证无需新训练；若坚持比较一个有效 learned detector，再先独立证明其 sanity 与 held-out coverage 合格。

## 资料边界

审查包是源资料的只读汇编。revision_base.md 仅增加块标记，方便标识拟议修订位置；它不是已修改的论文。原仓库研究文件未由本次审稿改写。Schema 6/roadmap 不含作者取舍，不授权写入。


## Attachment: Suggested-Reference Check (advisory, #1001)

建議文獻查核（腳本輸出，不是審稿意見；#1001）
已讀審稿席次：R2, R3（部分）。
未讀取：
- R2：報告裡沒有 suggested-references 區塊。
- R3：報告裡沒有 suggested-references 區塊。
沒有讀到任何可查核的建議文獻。


## Attachment: Reviewer Claim Check (advisory, #1002)

未运行：附加 judge 调用受当前 agent 用量限制影响；没有把未执行检查当作已验证结论。

## Attachment: Acronym Check (advisory, #849)

未运行：本轮没有完整论文正文文件，审查对象为研究材料汇编。
