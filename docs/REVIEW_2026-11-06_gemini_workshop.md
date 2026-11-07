# ToolReturn_UQ 代码与实验审查

审查版本为 `d0e7ba4`，目标为 AAAI 2027 Trust4RSI-Agent 的 4 页 short paper。以下现有结果来自已提交的轨迹和分数。Gemini 方案是待锁定的建议，未发出 API 请求。

## 现有结果与论文主张

6 组 Qwen 模型、tier 或重复运行配置共 3,780 条轨迹。1,260 条 toxic 轨迹中有 1,175 条实际触发投毒，1,150 条触发后记录了 `poisoned_answer_used`。相对全部 toxic 运行是 91.3%，条件于触发是 97.9%。两者回答不同的问题，应同时列出并按模型与 tier 拆分。相同的 210 个任务被重复使用，置信区间需要保留任务与表的聚类结构。3,780 条的 `anomaly_detection` 标记全为零；论文需说明检测器如何定义该标记，才能解释“零次质疑”。

建议论文聚焦一个运行时决策：面对表格工具返回的单个数值，当前可见上下文和模型自报置信度能否提示核验？现有证据限定在 6 张表、乘法扰动及两个 Qwen 模型。0o* 是依赖完整表采样分布与任务模板的参考分数，缺少最优性证明。随机 k 行曲线来自离线模拟，不能直接解释为增加行数后真实 agent 会改善。P5 的预测器未通过预设的校准和 sanity 检查，适合作为具体失败案例。

## 优先修正的实现问题

| 优先级 | 定位与证据 | 建议修正及验收 |
|---|---|---|
| P1 | `experiments/p4_score_zeroparam.py:52–59` 从 tier 得出 k 并直接取表头。Qwen3-4B T1 的 386 个已评分事件中，57 个 clean 和 58 个 toxic 事件之前通过 preview 暴露的行数为零。 | 以每个目标返回为界，在其之前的工具事件上重建实际 preview。对不足五行用真实行数，依赖 preview 的分数在无 preview 时记不可算，报告覆盖率和协议指定的系统级口径。T0 也要检查 min/max 是否确实下发。 |
| P1 | `experiments/p4_score_intrinsic.py:17–22` 先从事件端删除 ERROR，再与保留 ERROR 后续响应的列表 zip。4B T1r2 的 `lt_penguins_v3_unf_009` 第一步报错，第二步返回投毒值，当前选中了第一步的置信调用。这个例子恰好两次都报 50，熵和其他任务仍需核查。 | 采集时给目标事件和影子请求同一 event ID。旧轨迹按工具步骤和调用记录对齐，先建立对应关系再过滤，歧义计入缺失。对标量切片实际检查 scalar 条件。 |
| P1 | `experiments/p4_score_intrinsic.py:42–46` 对两类均存在、所有分数相等的表返回空值，再从表均值与 bootstrap 中删除。 | 此时 AUROC 应为 0.5。只在缺一类或无有效观测时记 NA。覆盖“常数两类、缺一类、全部缺失”三个测试用例，同时报告有贡献的表数。 |
| P1（Gemini 运行） | `experiments/p4_run.py:37,155,176–185` 模型注册表没有 Gemini，路径固定追加 /v1/chat/completions，且同一开关同时控制影子置信调用和 top-20 logprobs。现有置信度正则也允许超出 0–100 的数字。 | 启用独立的 provider 路由、verbalized 与 entropy 开关，严格校验单个 0–100 整数，保留原始响应、停止原因与缺失。API 的 400/401 应快速失败。用无密钥 fixture 验证 URL、请求体和响应解析；真实请求另做 smoke。 |
| P1（运行隔离） | `experiments/p4_run.py:87–101` 的 pandas 代理把未知路径交给真实 read_csv，模型生成的 Python 又在 API 客户端进程内执行。 | 正式运行前只开放已声明的数据集，用独立低权限工作进程执行模型代码，该进程不接触 API 凭据、桌面文件或网络。验收包含已知表可读和未知路径不可读。 |
| P2 | `experiments/p4_score_intrinsic.py:32–41,59` 两侧独立纳入事件，severity 明细用所有 clean 当对照。8B T1 的 199 条 clean 和 196 条 toxic 对应 195 个两侧均有的 task ID。 | 对“同任务配对”的主张使用双方都有分数的任务，并同时给出全体覆盖和同代码敏感性分析。按 severity 比较时，clean 使用同一批 task ID。把部署型全事件口径单列。 |

### 对 head-5 结果的现有数据核查

沿用仓库的标量选择和已存分数，以 (task_id, clean/toxic) 连回轨迹，在目标事件之前检查 preview_exposure.rows_exposed。各表单独计算 AUROC 后作等权平均，舍弃该信号缺一类的表。下表只是对已有分数分层，未重跑模拟或学习模型，也未将不可算事件补分。

| Qwen3，T1 | 标量事件 | 0a 范围检查 | 0d 重执行 | 0o* 参考 |
|---|---:|---:|---:|---:|
| 4B，原文件全部 | 386 | 0.541 | 0.549 | 0.582 |
| 4B，目标前实际 preview 五行 | 271 | 0.544 | 0.558 | 0.624 |
| 8B，全部均实际 preview 五行 | 393 | 0.533 | 0.534 | 0.571 |

仅筛选已看五行会改变任务组成，表内差值不能作因果解释。4B 的 0d 点估计变化小，但“所有 head-5 参考值都不超过 0.58”需要改。当前机器已有的 Python 环境（NumPy 1.26.4、pandas 2.2.3）运行 test_zeroparam.py 输出 ALL PASS，含 63,000 次子集检查；这套测试只覆盖共享统计实现，不覆盖轨迹对齐。仓库指定版本的端到端复现尚未执行。

## Gemini 执行顺序

1. **先锁定闭源外部复现。** 原始 P4 指定 gpt-5.4-mini；在能保留时间戳的单独协议提交中说明新增或替换为哪一版本 Gemini、选择依据、T1 场景和预算。H5 在 research-state.yaml 指向 subtle 的自报置信度；已有 73 个 subtle 任务。明确 primary 为该切片、负置信度、表内 AUROC及预定的区间判据，plausible+subtle 作可比的次要结果。事先决定缺失处理与配对、重试策略、任务顺序和如何记录模型版本。不根据观察到的 Gemini 效果更改阈值。
2. **先离线，再 20 个 clean smoke。** 本 checkout 缺少 data/toxicbench，先用 scripts/setup_toxicbench.sh 恢复固定提交。保持原 ReAct 提示、温度 0.7 和最多 8 步。用模拟响应检查协议和事件 ID，再以单独的输出目录跑仓库的 20-task smoke。区分可解析 final answer 与“途中零解析错误”；两者在当前脚本中容易混淆。其后用少量预指定的 clean/toxic 对验证 poison-once、目标数值匹配和置信调用，不看 AUROC 选协议。记录每条轨迹主调用与影子调用的 token 用量，再估正式费用。确认供应商 seed 支持；若不能保证固定 seed，记录为同设定独立重复。
3. **正式只补 T1。** 原 210 个任务，两个 clean 重复、一个 toxic，合计 630 条轨迹，API 请求数会更高。排除 smoke 的配置或输出混入。表一给 clean success、poison fired / 全部 toxic、used / 全部 toxic、used / fired 及检测率。表二给 verbalized 的覆盖率、同任务 AUROC、区间和每表样本量。0a/0d 用正确暴露行数离线算。仅当所选模型返回协议所需的 token 对数概率时才报告可比较的熵。区间跨判据时直接报告未决。即使 Gemini 更常质疑工具，这也是外推边界。
4. **投稿。** 建议按 4 页 short paper 排版。主图呈现离线随机抽行曲线，实际 head-5 agent 点单独标注；主表比较 Qwen/Gemini。正文明确当前只观察一次工具返回与后续行动，跨任务持久状态、工具版本漂移及长期自我演化留作未测试范围。若仍有时间，优先评估预先锁定阈值的核验触发率、clean 误触发率与额外调用成本，披露 poison_once 下重查可恢复真实值。官方截止 2026-11-20 AoE，双盲、非归档，可投 4 页短文或 8 页全文。

[Workshop 征稿](https://trust4rsi-agent.github.io/AAAI2027/) · [OpenReview](https://openreview.net/group?id=AAAI.org/2027/Workshop/Trust4RSI-Agent) · [Google Gemini OpenAI 兼容接口](https://ai.google.dev/gemini-api/docs/openai)


## 后续实验记录（2026-11-07）

新增固定返回、三种 context 的 Gemini pilot 已完成，独立于以上 P4 自由 agent 复现。结果、评分限制与 Qwen 复现命令见 [context pilot 报告](CONTEXT_PILOT_2026-11-07_gemini.md)。本条不替换以上历史审查。
