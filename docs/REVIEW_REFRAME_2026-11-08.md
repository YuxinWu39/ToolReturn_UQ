# 新版稿件与实验 A 的定点核验（2026-11-08）

审阅对象：main 的 554b2d0。用户提供外部 review 与新版稿件后，本轮核对 manuscript、exporter、保存的轨迹和 summary；没有修改被审稿件或实验代码，没有模型调用。本报告不是新的正式五席审稿，也不给录用概率。

## 判断

将 P4 行为与 k-sweep 作为主线、把 12-query pilot 作为同证据对照，是比上一版更完整的组织方式。此前撤回理论解释，不要求删除有效的描述性结果。上一版过度聚焦小 pilot 的问题成立。

当前更合适的一句话贡献：**在已测数值工具任务中，Qwen 对污染返回的自动采纳指标持续很高；已有统计核验程序的表现随可见样本预算增加而提高，并能从选定的相关样本中提取识错信号。这支持继续检验基于可见证据的返回值监控。** 系统部署收益与监控位置的必要性尚未被实验确立。

30–40%、55–65%、70% 均无已知校准依据；外部评审也标为主观。可以接受其写作建议，不应把这些百分比当作实验或投稿资源决策的可靠预测。

## 已核对的数字

- exporter --check：25 项证据、14 个来源文件、9 张表，通过。
- 4,410 = 7 组配置 × 210 任务 ×（两次 clean + 一次 toxic）。它不是 4,410 个独立任务；包含 clean 和 T1r2 重复运行。
- 正文 Table 1 展示 6 组配置，省略的 4B T1r2 有 202 次 poison fired、196 次自动 adoption，与 T1 同值。总轨迹数包含该组，必须脚注解释。
- Table 1 的 Qwen fired 条件采纳率 97–99%，Gemini 72/128，均能从 saved metrics 复核。它们是自动 poisoned_answer_used，分母是实际触发污染的 toxic runs，不是全部 4,410。
- 4B T1 的 preview/no-preview 为 141/144 与 55/58；T0 为 140/141 与 55/58。不能称精确相同，也没有随机化 preview 暴露。
- 固定跨 k 共同支持集为 168 个任务，0d 表内 AUROC 为 0.616628、0.646627、0.689233、0.745376、0.793369、0.839350。曲线在这六个已测预算点递增，值得保留。
- 新表的高/低 sanity 最小值约 0.976，来自保存的每 k sanity 项。实现 sanity_auc 使用 pooled AUROC，且基于该 k 的可计算事件；主曲线是跨 k 固定 168 任务的表内 AUROC。表注必须说明支持集和聚合方式，不能假装是同一组表内指标。若要主张共同支持集上的 gate，同一份缓存事件还需单独核对，不能用当前表直接替代。
- matched20 原始 10/12 检出、1/12 误报和 F12 的 161/240、14/240 保持成立。0.917 与 0.818 是不同条件下的估计对象；F12 没有新增模型回答。

## 新版尚需修改的主张

| 位置（manuscript.md） | 问题 | 可保留的说法 |
|---|---|---|
| 第 7、16、49、63、114 行，any checker | 测过的一个/几个程序表现弱不能证明任何检查器证据不足；未测 human | 在指定检查与抽样方式下，五行条件表现较弱；k-sweep 为方法的经验曲线 |
| 第 7、15、45、114 行，same rate / Seeing rows did not help | 自选 preview 行为与任务/模型轨迹有关，未做因果或等效检验 | 观察到两组的自动采纳率均高；不据此识别 preview 效果 |
| 第 15 行，four observation-context tiers | 实际独立内容条件为 T0/T1/T3；T1r2 是 T1 的重复 | 三个 context tiers、七组配置，含一个 T1 复测 |
| 第 114 行，agents almost always | Gemini 56% 不能写成几乎总是 | Qwen 97–99%，Gemini 56%，分别限定 fired runs |
| 第 7、11 行，没有 error 就没有 retry | 没有显式错误信号，不等于不会重查；已有 Gemini 恢复轨迹 | schema/执行状态未显式暴露数值错误，仍可能有后续调用 |
| 第 47 行，37/50 later errors | 时间顺序不能省略：首次后续 Python success/error 为 23/27，10 条先成功后报错 | 保留时序计数，不把 37 条全归于错误触发的重试 |
| 第 18 行，intrinsic did not pass gates | 缺少 live sanity 与实测失败不同 | intrinsic sanity 未采集；learned scorer 实测 gate-failed |
| 第 88、96、98、114 行，cheap/runtime attribution/recovery | 未测成本、版本干预、执行重试成功或 runtime 与其他位置的比较；版本日志只帮助追踪，不自动识别因果 | 候选接口/可验证系统假设；监控需测策略、成本、误报和后续动作 |
| 第 108 行，None of these | 五篇文献的局部比对不能建立普遍不存在；Outcome Monitors 已提供端到端监控与恢复控制 | 对已核对的方法明确区别：本研究约束到 agent 实际可见样本上的数值统计一致性 |

可以集中讨论重复局限，但样本单位、相关性/因果性、方法范围、尚未测量的部署收益，必须在相关主张处保持准确。把限制统一挪到末尾不能修复正文的强断言。

## 实验 A：赞成方向，建议先 Gemini，设计还需锁定

目前只是建议，**不是已经提交的 preregistration，也不是批准启动 API 的记录**。本轮不跑模型、不消费 API。Qwen 可在同一 manifest 上由用户后续复现；Gemini 单模型实验只能支持该模型的干预结果。

### 先修正可行性

对已有 210 任务进行不依赖新模型输出的查询清点（op=mean、有 filter、去重 column/filter、>=20 个匹配有限目标值、总体均值正且有限）：

| 表 | 满足该初筛的不同查询 |
|---|---:|
| Abalone | 5 |
| Auto MPG | 7 |
| Bike | 8 |
| Penguins | 7 |
| Student | 5 |
| Wine | 5 |

总量可以取 36 个，但不能做到每表 6 个。推荐每表按预定顺序取 5 个、共 30 个；也可预定不等额表内样本或先生成新查询。冻结前还需检查数值 tolerance 与候选非等价。已有表/查询都被项目看过，不能称全新表外泛化检验。

### 核心三组

| 组 | 看到的信息及操作 | 能回答的问题 |
|---|---|---|
| A：raw | query/code、同一份 matched20、候选值 | 当前单次提示审计的对照 |
| B：raw + check | A + 由相同行、相同 0d 实现计算的区间/样本量/flag；不含 truth 或标签 | 提供这套核验辅助是否改善判断 |
| C：raw + code access | 同样二十行、相同候选，允许有限 Python/统计工具操作，不给全表 | 可执行计算条件下的表现及额外成本；不能单独识别“意愿” |

B 应清楚区分 compatible 与 verified-correct；flag 不提供修正后的全表答案。C 的工具只能读展示的行，限定请求/工具调用预算并保存代码、返回、错误和实际成本。不要声称三组计算量相等；C 未调用工具本身也是需要报告的观测。

B 对 A 的改善只识别辅助包的总效果，不能单独区分警告文字、数值摘要和 flag。若主张是“统计内容本身优于提醒”，需额外 generic-caution 对照；若只做三组，贡献应限定为辅助包干预。还应并列直接 0d 固定规则，不给它增加模型调用。

### 重复与比较

建议每查询冻结 3 份独立 matched20 行样本；每份样本在三组和所有候选之间完全相同，一格一次模型回答。这测试证据抽样与回答的混合变异，不等于同一份样本上的三次模型重复。也可以选择固定样本三次 completion，但必须明确改测什么，不能将两者混称。三组分开开启会话，按 query/draw 分块交错随机执行，避免时间/服务状态与组别绑定。

每个查询交叉 clean、×1.10、×1.50，解决当前 severity 与 query 绑定的问题。这个版本只研究向上污染；若要同时检验向下污染，加入两种倒数后变为五个候选，不要再沿用三候选预算。

30 queries × 3 draws × 3 candidates × 3 arms = **810 个计划完成的情境轨迹**。这不是 810 次 API 调用：C 是多轮，另有校验单元、sanity、可能的 transport 尝试。加 generic-caution 第四组则为 1,080 条；加入向下污染的三组版本为 1,350 条。需通过不计入主分析的小规模工程 smoke 测量实际请求、usage、耗时，再估算费用，不保证半天或某个 token 总数。

### 预先锁定的结果与解释

主对照 B−A：每查询 clean acceptance 减去两个 corrupted acceptance 的均值，再在 draws 内平均、表内平均、六表等权。保持同一任务/证据配对，公开表内、严重度、覆盖和失败分母；描述性表聚类区间仍只有六个表，三次重复不会变成 90 个独立任务或更多表。

C−A/C−B 可作预先声明的次要比较；若多模型/多主假设须规定多重比较处理。主结论不以模型 confidence AUROC 为依据。监控程序先在冻结证据上验证 sanity 与缺失支持，不能依据效能挑选“容易”的证据或只报告通过的查询。

同时报告 clean accept、错误接受、最终数值答案错误、abstain/null、格式失败、工具调用/错误、input/output usage、耗时、B 中接受已 flag 值或拒绝 compatible 值的频率。**弃答不等于回答正确；不能把一律拒绝写成准确率提高。** 若要声称重查恢复/净系统收益，还须明确后续动作策略及可用源权限并实际执行，而不是仅测最终一次 accept/reject。

成功、无效或损害都按预定规则保留。即便 B 改善，也不能证明检查只能放 runtime、证明新的算法或识别模型内部机制。若失败，也不能证明所有 monitor 无用。

## 投稿建议

采纳新主线并修正上述过强句，再做一个小而完整的干预，比只放大旧 pilot 更有价值。先 Gemini 是合理范围控制；Qwen 后续复现可增强外推。四页版应将直接已测结果、候选系统接口与后续实验三者写清。

五篇新增参考的标题/作者与官方 arXiv 记录匹配；这不是全领域 novelty 审计。Outcome Monitors 已研究监控回执和恢复收益，因此“runtime monitor 有用”本身不是本项目独有贡献。目标 workshop 官方页面欢迎负结果/系统研究，但不据此给录用概率。

来源：
- https://arxiv.org/abs/2608.19303 及 https://arxiv.org/html/2608.19303v1
- https://arxiv.org/abs/2610.09793 及 https://arxiv.org/html/2610.09793v1
- https://arxiv.org/abs/2609.05587
- https://arxiv.org/abs/2610.10062
- https://arxiv.org/abs/2610.08097
- https://trust4rsi-agent.github.io/AAAI2027/

设计辅助：experimental-design / hypothesis-generation skills。资源引用：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents. https://doi.org/10.48550/arXiv.2609.00065 。它是开发流程来源，不是本研究效能证据；不要求在正文占据贡献位置。

核验快照 SHA-256：

- `paper/manuscript.md`: `f931defdcc019a21e51b506cc207bba253974617412e81914f3676e773212f34`
- `experiments/export_paper_evidence.py`: `e94dff85a8bd2ce9d7bc7241cdc4f42d27884ca599e22d11e1607028cfdfe889`
- `data/ours/tasks/large_tables_v2.jsonl`: `266432d9ea64f13d401ac59138fb3995e9be6b511970bf4998268e7097047f93`
- `data/ours/ksweep2/summary.json`: `cccd209a39b6ad0a82489c52e2139ad6641235afc156a930c23a74f0fca16118`
