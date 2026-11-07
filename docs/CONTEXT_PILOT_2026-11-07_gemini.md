# Gemini 固定返回 context pilot（2026-11-07）

本轮是显式要求模型审计工具返回的单次判断实验。它与此前允许模型自行调用工具的 P4 实验分开。

完成 72/72 个实验条件，格式有效 67/72；实际收到污染条件响应 36 条。每个条件一次回答，共 12 个查询、6 张表；72 个回答不能当成 72 个独立查询。

| 展示的 context | 接受正确返回 | 接受错误返回 | 最终答案照抄错误值 | 正确返回时答对 | 错误返回时答对 |
|---|---:|---:|---:|---:|---:|
| 前 5 行 | 12/12 | 9/12 | 9/12 | 12/12 | 0/12 |
| 全表随机 20 行 | 12/12 | 7/12 | 7/12 | 12/12 | 0/12 |
| 筛选后随机 20 行 | 11/12 | 5/12 | 5/12 | 11/12 | 0/12 |

“接受”读取 decision；“照抄错误值”读取最终 answer，并要求它匹配错误值且不匹配真值。两者回答不同问题。拒绝、犹豫或弃答都不自动等于恢复正确答案。这些分子只计严格格式有效的回答；分母包含格式失败，因此下降可能部分来自输出失败。

| Context | 正确返回：拒绝 / 犹豫 / 格式失败 / 弃答 | 错误返回：拒绝 / 犹豫 / 格式失败 / 弃答 | 正确 / 错误返回的平均 confidence |
|---|---|---|---|
| 前 5 行 | 0 / 0 / 0 / 0 | 2 / 0 / 1 / 2 | 98.5 / 96.1 |
| 全表随机 20 行 | 0 / 0 / 0 / 0 | 3 / 1 / 1 / 4 | 98.9 / 92.1 |
| 筛选后随机 20 行 | 0 / 0 / 1 / 0 | 5 / 0 / 2 / 5 | 98.6 / 97.0 |

弃答是 answer=null，与 decision 的拒绝/犹豫可能重叠，不能把这几列相加。

## 预先锁定的主对照

每个查询的区分度 = 接受正确返回 − 接受错误返回；范围 −1 到 1。下面的效应是两种 context 的区分度差，按表等权，区间为六表 cluster bootstrap 的描述性区间。

| 对照 | 差值（百分点） | 95% 描述性区间（百分点） | 查询 / 表 |
|---|---:|---:|---|
| matched20_minus_head5 | +25.0 | [+8.3, +41.7] | 12 / 6 |
| matched20_minus_random20 | +8.3 | [-16.7, +33.3] | 12 / 6 |
| random20_minus_head5 | +16.7 | [-16.7, +41.7] | 12 / 6 |

主对照是 matched20 − random20，两组都给 20 行。random20 − head5 同时改变行数和抽样方式，不能把它称为纯粹的“多给 context”的因果效应。抽样说明文字也属于干预。

主对照区间跨过 0；本轮不能确认“相关 20 行优于随机 20 行”。9→7→5 是原始严格计数，不能直接当成语义识错能力的改善。

| 完整有效配对敏感性 | 差值（百分点） | 95% 描述性区间（百分点） | 查询 / 表 |
|---|---:|---:|---|
| matched20_minus_head5 | +30.0 | [+10.0, +50.0] | 9 / 5 |
| matched20_minus_random20 | +10.0 | [+0.0, +30.0] | 8 / 5 |
| random20_minus_head5 | +16.7 | [+0.0, +33.3] | 10 / 6 |

有效配对分析改变了任务与表的支持集；它不是缺失无偏的证明。主对照的逐表贡献中，Abalone 的正贡献涉及相关样本组的污染响应截断，Student 的负贡献涉及相关样本组正确返回的 JSON fence 失败；Penguins 的正贡献对应一次有效判断由接受错误值变为拒绝。格式失败和语义判断应分别报告。

## 逐查询与严重度

| 表 / 查询 | 扰动倍数 | 严重度 | 前 5 行：正确 / 错误 | 随机 20：正确 / 错误 | 相关 20：正确 / 错误 |
|---|---:|---|---|---|---|
| lt_abalone_fil_016 | 1.1 | subtle | accept / accept | accept / accept | accept / accept |
| lt_abalone_fil_018 | 1.5 | plausible | accept / invalid | accept / accept | accept / invalid |
| lt_auto_mpg_v4_fil_013 | 0.909091 | subtle | accept / accept | accept / accept | accept / accept |
| lt_auto_mpg_v4_fil_014 | 0.666667 | plausible | accept / accept | accept / invalid | accept / reject |
| lt_bike_v4_fil_011 | 1.1 | subtle | accept / accept | accept / accept | accept / accept |
| lt_bike_v4_fil_012 | 1.5 | plausible | accept / reject | accept / reject | accept / reject |
| lt_penguins_v3_fil_013 | 0.909091 | subtle | accept / accept | accept / accept | accept / reject |
| lt_penguins_v3_fil_014 | 0.666667 | plausible | accept / reject | accept / reject | accept / reject |
| lt_student_fil_012 | 1.1 | subtle | accept / accept | accept / uncertain | accept / invalid |
| lt_student_fil_018 | 1.5 | plausible | accept / accept | accept / accept | invalid / accept |
| lt_wine_quality_fil_012 | 0.909091 | subtle | accept / accept | accept / accept | accept / accept |
| lt_wine_quality_fil_014 | 0.666667 | plausible | accept / accept | accept / reject | accept / reject |

| 严重度 | Context | 接受正确返回 | 接受错误返回 | 照抄错误值 |
|---|---|---:|---:|---:|
| plausible | 前 5 行 | 6/6 | 3/6 | 3/6 |
| plausible | 全表随机 20 行 | 6/6 | 2/6 | 2/6 |
| plausible | 筛选后随机 20 行 | 5/6 | 1/6 | 1/6 |
| subtle | 前 5 行 | 6/6 | 6/6 | 6/6 |
| subtle | 全表随机 20 行 | 6/6 | 5/6 | 5/6 |
| subtle | 筛选后随机 20 行 | 6/6 | 4/6 | 4/6 |

严重度与查询绑定、扰动方向与表绑定；切片仅作描述，不能推断严重度或方向的因果作用。

## 结果后诊断（不改变预注册评分）

严格格式失败 5 条：3 条是完整 JSON 外包 markdown fence，2 条因 length 截断。没有修复后替换评分，也没有重跑这些条件。

10 条有效 reject 中，10 条 confidence≥95。这与提示中“工具值正确的信心”定义冲突，符合模型将其理解为“对当前判断的信心”的解释。因此，不能把这些 confidence 当成有效的工具正确性概率，更不能据此宣称信号无效或有效。

若干 reason 引用了标准数据集的总体均值，例如被污染的 Gentoo 体重返回旁写出 “Palmer Penguins ground truth (~5076 g)”，而当前样本均值不同；Bike 的 head5 条件也引用总体湿度范围。这与调用模型的已有知识相容，但不能仅凭解释证明模型的内部机制。因此，不能声称核验仅依靠可见样本；后续需要私有生成或重命名/变换后的数据控制。

## 复现与限制

- 模型：gemini-3.8-flash；低 reasoning，默认采样；finish_reason：{"length": 2, "stop": 70}。
- 已返回响应用量：输入 101,889、输出 5,878、总 token 128,020。
- 以上是接口原始 usage 字段；total 比 prompt+completion 多 20,253，接口未在此另行拆分，不能只用可见 completion 估算账单。
- 内部 HTTP 重试次数未知；失败日志只保留重试耗尽的最终失败，不是总 API 尝试数或账单。
- 无 live 极端污染 sanity arm，因此 confidence AUROC 按仓库门槛 withheld，不据此下检测性能结论。
- 每条件一组冻结样本、一次回答；只有 12 个按规则选出的 filtered-mean 查询，未重复抽样或模型采样。
- 这里测的是被明确要求审计时的行为；不等于自由 agent 会主动核验，也不证明一个新方法优于已有方法。
- 结果不能直接用来判断论文可录用。下一轮应由 Qwen 复现、扩大查询与抽样重复，再单独做 sanity 和技术方法对照。

Manifest SHA256：`7263b5dcd25ccf3c4463ffe6778243a3f953a153c55f0c493d9714cd0dc99983`。协议提交 `bfaf713`，代码 `7e5c662`，冻结请求 `5da0d36`，采集前说明 `41473be`。

原始数据：`data/ours/context_pilot/20261107/gemini-3.8-flash/responses/`；汇总：同目录 `summary.json`、`scored_responses.json`。

Qwen 启动自己的 OpenAI-compatible 服务后，从仓库根目录执行（模型服务名称需为 qwen3-8b）：

```bash
python experiments/context_pilot.py run \
  --manifest data/ours/context_pilot/20261107/manifest.json \
  --output data/ours/context_pilot/20261107/qwen3-8b \
  --model qwen3-8b --base-url http://127.0.0.1:8000/v1
python experiments/context_pilot.py summarize \
  --manifest data/ours/context_pilot/20261107/manifest.json \
  --output data/ours/context_pilot/20261107/qwen3-8b
```

直接复用 manifest，不要重新 prepare。需要同版 context_pilot.py、p4_run.py、zeroparam.py 和 ToxicBench 依赖。Gemini 续跑也只补没有完成响应的条件，已返回但格式失败的回答不会重跑。
