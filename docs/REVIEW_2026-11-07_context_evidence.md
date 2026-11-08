# A-CTX-EVIDENCE 独立预检与结果复审（2026-11-07）

按 program.md milestone 要求，由独立子 agent 只读审查。角色分离不保证统计独立的错误过程。

预检指出两处问题，均在真实测量前修复并提交：severity 不得绕过 context sanity gate；共同支持集需要保留模型四类决策与 baseline 决策分解。新增回归检查覆盖前者。

结果复审：PASS-AS-EXPLORATORY，未发现新的泄漏、计算或协议错误。只读取产物，没有重跑 bootstrap。

- 36 组 feature、288 个事件键唯一；用保存的范围/区间独立重算所有 score，一致。
- 用两类分数排序复算 matched20 的 0a / 0d AUROC，与汇总一致。
- 四个失败 context/method 的正式 AUROC、severity 结果及跨 context 对照没有绕过 gate。
- 例外：Bike registered clean false flag；Abalone Whole_weight 与 Student absences subtle 错误仍兼容。
- 支持固定样本存在可提取信号；不证明特定内部机制、普遍胜过模型、bootstrap 有有限总体覆盖保证或新算法。
- 相同数值证据不等于相同表示、计算和成本。Gemini 格式缺失、公开数据先验、Qwen raw 未归档的限制继续保留。

推荐下一步：新生成表上比较原始样本与由同样样本计算的统计摘要；保留直接统计基线、clean 和 sanity 控制。另需独立抽样重复确认样本敏感性。

数值与图来自脚本生成的 [结果报告](CONTEXT_EVIDENCE_2026-11-07.md)。
