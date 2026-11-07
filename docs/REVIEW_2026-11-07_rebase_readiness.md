# ToolReturn_UQ 更新复核与投稿价值评估

评估日期为 2026-11-07。评估快照为本地 main 的 30a7825，远端基线为 fa2c280。结论是值得继续完成一篇 4 页 workshop short paper。当前材料的主要价值是可追溯的实证分析，贡献强度为中等增量。形成可投版本仍需统一主张、结果表和近邻文献对照，仓库目前没有论文正文或投稿 PDF。

本报告使用 academic-paper-reviewer 的修订核验、证据锚点和反方检查框架，以及 scientific-critical-thinking 的设计与证据评价框架。实际执行为单模型项目级证据复核，状态为 NOT_CALIBRATED。评估对象是代码、原始轨迹、结果表、协议和论文定位。

## Git 同步结果

执行了 git pull --rebase origin main。远端新增 fa2c280，包含实际 preview 暴露、影子调用对齐、常数 AUROC 和 read_csv 的修复。三个本地 Gemini 提交已重放为 1a1c3ee、1eb6b14、30a7825。

findings.md 与 research-log.md 各有一处末尾追加冲突，均保留了远端评分修正和本地 Gemini 结果。工作分支已恢复 main，位于 origin/main 之上三个提交。Gemini 原始 manifest 中的旧提交和哈希记录对应采集时的历史版本，应该保留这些历史证据。后续复现可注明原采集版本与整合后的版本。旧 Gemini 提交链保留在本地 codex/gemini-pre-rebase-20261107 分支，便于解析历史协议与实现的提交号。

## 先前问题逐项核验

| 先前问题 | 当前判定 | 本次核验和残余限制 |
|---|---|---|
| 按 tier 上限评分，即使 agent 没看 preview | 已修复当前数据 | exposure_before 按目标事件之前的 preview 重建行数与 min/max。核对六组评分文件的 2,318 行，元数据与轨迹全部一致，无 k=0 时仍有 0d、0o* 或 0r_log 的情况。 |
| 删除 ERROR 事件后导致置信度错位 | 已修复当前数据 | completion_after 保留 ERROR 对应位置并跳过解析重试。独立依据 raw_actions 重建调用次序，核对 3,590 个后续响应，未发现错配。 |
| 常数分数被当作 NA，移出表均值 | 已修复 | auc_or_none 在两类均存在且分数恒定时返回 0.5。缺一类和全部缺失仍返回 NA。共享测试全部通过。 |
| 非标量事件被混入 intrinsic 评分 | 已修复当前口径 | target_event 现在检查事件本身的单数字条件。低覆盖率已经暴露出来，尤其影响 Gemini。 |
| severity 的 clean 控制组没有限定同任务 | 已修复分层表 | severity 控制组取相同 task_id，代码另报 paired 结果。H1 的判据列仍使用 P+S 全可评分事件，paired 列为全 severity，建议投稿表统一主切片与配对口径。 |
| read_csv 能读任意未知路径 | 该入口已修复 | 未声明的文件现在返回 FileNotFoundError。本次用无敏感信息的临时文件复现了拦截。 |
| 模型代码缺乏完整执行隔离 | 部分覆盖 | Gemini 在 macOS 使用独立 Seatbelt worker。其他运行路径仍沿用原环境，SAFE_BUILTINS 中可导入模块。相同临时文件通过默认环境中的 builtins.open 仍可读，通用路径不能宣称完整隔离。 |
| Gemini 的 URL、参数和严格置信解析 | 已验证可用 | Google 官方路由已完成 630 条轨迹。四个回归测试通过。越界或附加文本的置信答案记为缺失，返回模型、finish reason 和用量均有记录。 |

对应实现见 [共享评分逻辑](/Users/yuxinwu/Desktop/ToolReturn_UQ/experiments/p4_common.py:16)、[intrinsic 事件选择](/Users/yuxinwu/Desktop/ToolReturn_UQ/experiments/p4_score_intrinsic.py:22)、[read_csv 入口](/Users/yuxinwu/Desktop/ToolReturn_UQ/experiments/p4_run.py:100) 和 [worker 启用条件](/Users/yuxinwu/Desktop/ToolReturn_UQ/experiments/p4_run.py:299)。

## 重新运行与结果

在独立的临时本地 checkout 中运行正常评分入口，保留项目中的原文件。下列三份 Qwen 输出和 Gemini summary 与已提交文件逐字节一致。

| 复算项 | 结果 |
|---|---|
| Qwen3-4B T1，实际 exposure | 0a 0.544，覆盖 70%；0d 0.554 [0.51, 0.62]，覆盖 53%；0o* 0.611 [0.54, 0.69]，覆盖 48% |
| Qwen3-4B T1r2，P+S verbalized | 0.554 [0.50, 0.61]，H1 未确认 |
| Qwen3-8B T1，P+S verbalized | 0.527 [0.48, 0.56]，达到原 H1 阈值 |
| Gemini T1 summary | 与已提交 summary.json 完全一致，H5 未确认，subtle 有效配对 7/73 |
| test_p4_common.py | ALL PASS |
| test_p4_gemini.py | 四项测试通过 |
| test_zeroparam.py | 25/25 sum-type 检查通过；63,000 次子集对齐，零不匹配；ALL PASS |

另对同一 P+S 切片同时要求两个标签均有分数，4B T1r2 的 verbalized 为 0.555 [0.505, 0.606]，162 个任务；8B T1 为 0.533 [0.498, 0.565]，164 个任务。现有 H1 判定在这个敏感性分析下保持一致。该检查支持配对后结论的稳定性，主结果表仍应明确自身总体。

## 剩余的重要问题

### P1，论文的“信息上限”主张超出目前证明

oracle_law 使用完整表、真实 theta 和任务模板的抽样分布，score_0o_star 再用偏差和 IQR 构造距离分数。这定义了一个具体的特权参考检测器。当前实现和材料没有证明其达到 Bayes 最优，或给所有使用相同观测的检测器提供统一 AUROC 上界。现有 findings 也记载 0r_log 在较大 k 时可以超过 0o*，因为使用的信息摘要不同。

因此，0d、0o* 等分数之间的差可以作为经验参考差距；把它们解释成严格的信息容量分解，需要额外模型假设与理论论证。最经济的修改是使用“经验检测曲线”“特权参考”和“已测方法的差距”等术语，把论文贡献放在受控观测条件下的实证表现。

证据见 [oracle_law](/Users/yuxinwu/Desktop/ToolReturn_UQ/experiments/zeroparam.py:319)、[0o* 距离分数](/Users/yuxinwu/Desktop/ToolReturn_UQ/experiments/zeroparam.py:344) 和 [当前中心主张](/Users/yuxinwu/Desktop/ToolReturn_UQ/findings.md:219)。

### P1，主结果入口仍没有完整吸收修正

findings 的新修正段已说明 4B 的 0o* 从约 0.58 变成 0.61–0.62。README 仍写“nothing tested separates”并把 k 曲线解释为信息限制，旧 F5/F6 标题仍有“无信息”和“没有方法超过 0.58”的表述。论文起草时容易从旧标题抽取已经失效的概括。

建议给历史段落增加明确的后续修正指针，并在论文摘要与主表中使用最新的、带覆盖率的实际暴露结果。4B verbalized 的上界仍超过 0.60，有限检测性能的点估计也不能推出所有方法完全不含信息。置信区间只基于六张表，还应保留每表结果和对固定数据源的范围说明。

证据见 [README 概括](/Users/yuxinwu/Desktop/ToolReturn_UQ/README.md:21) 和 [评分修正段](/Users/yuxinwu/Desktop/ToolReturn_UQ/findings.md:365)。

### P1，Gemini 提供的是外推边界，H5 证据仍稀少

Gemini 的 128 次实际投毒中，72 次采用污染值，50 次在后续调用后恢复；35 次第一投毒返回满足单标量口径，93 次为非标量。H5 在 73 个 subtle 任务中只有 7 个有效配对，来自三张表，AUROC 0.556 [0.500, 0.667]。模型采样参数也不同于 Qwen。

这些数据支持报告该模型在当前接口和 poison_once 下的行为。进一步判断模型本身的鲁棒性，需要匹配任务、输出格式、证据和调用预算。50 个恢复案例中有 37 个在投毒后出现过工具错误，重试、额外正确证据和主动核验的作用尚未分离。关键词 anomaly_detection 为零，也不能概括为所有实际轨迹都没有质疑或核验。

证据见 [Gemini 结果](/Users/yuxinwu/Desktop/ToolReturn_UQ/findings.md:416) 和 [完整汇总](/Users/yuxinwu/Desktop/ToolReturn_UQ/data/ours/p4/gemini-3.8-flash/T1/summary.json)。

### P2，论文比较应固定主切片和方法支持集合

零参数方法之间的覆盖率不同，0a、0d、0o* 的现有表均值可能基于不同的事件集合。以它们的 AUROC 差判断 estimator loss 前，应在同一可评分支持集上比较，并同时展示全任务覆盖率。H1 的 paired 列也应直接针对判据采用的 P+S 切片。现有配对敏感性分析说明两项 T1 verbalized 判定较稳定，但不能代替清楚的报告口径。

证据见 [H1 计算入口](/Users/yuxinwu/Desktop/ToolReturn_UQ/experiments/p4_score_intrinsic.py:65) 和 [零参数评分入口](/Users/yuxinwu/Desktop/ToolReturn_UQ/experiments/p4_score_zeroparam.py:93)。

### P2，P5 只能说明这个 scorer 配置失败

该配置未通过自己预设的 sanity 和 coverage 标准。这是可报告的负结果，能说明小型清洁数据预测器在该目标上的局限。以它支持整个 learned detection 类别失效，证据不足。四页正文建议把重点留给可解释的检测基线与观测条件，P5 细节可进入附录。

证据见 [F8](/Users/yuxinwu/Desktop/ToolReturn_UQ/findings.md:334)。

## 科研价值与近邻文献

我对原创性的判断是中等增量，主要来自数值工具场景中的定量观测预算实验，以及将 detector 性能、真实暴露、覆盖率和 agent 后续行为放在同一套轨迹中审计。

“工具错误会误导 agent”已有直接先例。ToxicBench 已覆盖污染采用、检查与恢复，其附录 E.2 还在三张公共表上用共享初始轨迹比较部分和完整字段污染。论文需要说明自身增加的 k 级观测预算、抽样方式及检测指标实验。单纯扩大任务数的说服力有限。[ToxicBench 原文](https://arxiv.org/html/2609.37153v1)

“在 tool return 到达时检查故障”也已有直接先例。Robustness Analysis 已在这个边界测 schema/context likelihood 与合法动作分布，并讨论 token entropy 的格式退化问题。本文可以贡献数值扰动与观测预算下的系统分析，相关工作中应正面比较这套检测视角；目前的动作文本 token entropy 只覆盖 intrinsic UQ 的一个具体实例。[Robustness Analysis 原文](https://arxiv.org/html/2608.22676v2)

实际反证是否在首次使用前可见，已经是 SSCBench 的核心问题。本文的差异可以是把证据预算具体化成抽样行数、行选择与检测性能曲线，实际 exposure 审计本身的首创性需要谨慎表述。[SSCBench 原文](https://arxiv.org/html/2610.11514v1)

轨迹指标与行为含义之间的差异已有专门审计工作。Gemini 的关键词零检出与后续调用恢复之间的区别，需要据此解释。[Trace 与标签审计](https://arxiv.org/abs/2610.30491)

上述判断来自本次对四篇近邻原始材料的定向核查，文献覆盖范围仍有边界。现有 bibliography 中“全部 verified”的标签也应与具体版本、完整作者和访问记录对应。

## 最强反方意见与我的判断

最强反方意见是，六张表上的抽样误差会随样本增加下降，这个现象本身符合统计常识；工具污染和 agent 盲从已有基准；两个 Qwen 属同一家族；小型 scorer 又未通过 sanity。若只把这些事实串联起来，独立贡献偏弱。

能够回应这条意见的证据应是可操作的测量结果，例如在同一任务和预算下，实际暴露、抽样代表性、可评分覆盖率如何共同改变检测结果，哪些自报信号并未补上这一差距，以及 agent 的额外工具调用如何改变最后结果。这能形成有边界的 workshop 实证贡献。当前已有大量材料可支持这个方向，严谨的主表和针对性的观测对照会显著增强论证。

## 投稿建议

建议目标为 Trust4RSI-Agent 的四页 short paper。官网明确接收负结果，提供四页短文与八页全文形式，采用双盲评审，截止为 2026-11-20 AoE，并声明 non-archival。研究与其工具接口、观测和审计分题相关。当前实验集中在静态任务的工具返回边界，尚未测长期状态或 agent 演化，引言需要解释这项边界研究如何帮助运行时审计。[官方征稿](https://trust4rsi-agent.github.io/AAAI2027/)

建议主线为“可见证据预算如何影响数值工具返回的错误检测”。候选英文题目为 *Detecting Corrupted Numeric Tool Returns Under Limited Evidence*。

形成可投稿件的最小工作包如下。

1. 统一摘要、README、图注和主表中的范围。明确 0o* 的参考性质、模型名称、实际暴露与覆盖率，以及 H1/H5 哪些判据未确认。
2. 用一张主图呈现实际检测器随观测预算的性能与覆盖率。若补一个实验，优先预先锁定同一批任务、相同 k 下的 head 与 random 抽样对照，固定统计量、扰动和共同支持集合。这样能分辨行数与代表性的影响，可先在离线模拟完成。
3. 用一张行为表区分全部 toxic、实际投毒、采用、后续证据调用和恢复；Gemini 同时标明单标量覆盖及重试限制。
4. 用精简的相关工作对照表解释相对上述四篇近邻的增量。保留六表限制、一次投毒和失败 scorer 的范围说明，形成匿名四页稿件与可复现附录。

我的投稿判断是“值得完成上述修订后投四页 workshop”。当前材料尚不足以作直接提交判断，因为正文、摘要、图和匿名附件仍未形成。代码核心评分修复已经通过核验，眼下的主要工作转向论文主张、比较口径与贡献呈现。

## 工具与方法引用

[academic-paper-reviewer skill](/Users/yuxinwu/.codex/skills/academic-paper-reviewer/SKILL.md) 提供修订核验和审稿证据锚点框架。[scientific-critical-thinking skill](/Users/yuxinwu/.codex/skills/scientific-critical-thinking/SKILL.md) 提供设计、混杂、统计解释和结论范围的评价框架。

Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents. 本次核对的 arXiv 页面最新版为 v2。[论文记录与 DOI](https://doi.org/10.48550/arXiv.2609.00065)
