# Gemini Experiment A（2026-11-08）

用户授权的三组配对干预，使用稳定模型 `gemini-3.8-flash`。正式清单：30 查询、六表，每查询三份独立 matched20 样本；每份样本交叉 clean、×1.10、×1.50 和 raw/check/code，合计 810 条轨迹。一格一次模型会话，code 组最多三次 Python、四次模型请求。三份样本不是三个新查询。

## 三组及主指标

- raw：query/code、20 条展示行、候选值。
- check：同样信息，加同一批行算出的 0d 区间、样本量、score 和 flag。无总体真值或标签。
- code：同样展示行，允许在凭据隔离的 macOS Seatbelt 子进程中执行 Python；每次工具调用开启新进程，只接收展示 CSV 和代码；Python 变量不会跨工具调用保留，聊天记录中的输出会保留。进程不能读总体 CSV、宿主文件或网络。CPU/墙钟/输出预算固定。

主效应 B−A：clean acceptance − mean(两类 corruption acceptance)，先对 draws、查询、表按协议聚合。2,000 次配对六表 bootstrap 为描述性区间。联合收益规则要求 discrimination 差的区间下界 >0，clean acceptance 差的下界 >=−0.05；不把它称作经功效设计的总体非劣性结论。C 比较是预定次要/探索性。弃答不是数值回答正确。

## 注册与工程记录

| 记录 | 提交 |
|---|---|
| 初始完整协议 | `89734f4` |
| 合成 smoke 后并发/请求计账修订，正式响应前 | `9ccf2bd` |
| 小量纲 numeric tolerance 修订，成功输入冻结前 | `880084a` |
| 正式实现 | `1be20ce` |
| 主输入冻结，正式模型请求前 | `0a8877b` |

最初 prepare 在 Abalone 停止：旧绝对容差 0.01 与小均值的10%错误重叠。没有成功主清单或主模型调用。新审计数值容差固定为 min(旧容差,2%×|truth|)，保留旧容差；主 acceptance 指标未改变。不能把新数值答案评分与旧 P4 分数混用。

九项测试包括：相同证据与候选配对、完成的无效回复不重生、length/refusal 终止、空 envelope、部分失败成本、主效应合成例、真实沙箱均值及源文件读取拒绝。六条独立合成 smoke 全部 strict-valid，八次模型请求、两次真实可见行 Python，无 HTTP 错误；不计入效能样本。smoke 原始来源哈希保留，不用新版覆盖。

主清单 canonical SHA-256：`350f5a3b18b97b434b517e9b08011f19c6c92c682e71abebde214ef66dcc6a07`。主证据90份均 finite，0d extreme-value sanity 的表内 AUROC=1.0。sanity 通过不代表区间校准或部署保证。

## 文件与执行

数据目录 `data/ours/experiment_a/20261108/`：manifest.json、features.json、sanity.json、runtime.json、config.json、逐条 responses/、status.json。独立 smoke 在 smoke/。原始模型响应、逐次 payload/message 哈希、开始/结束、HTTP 尝试、usage、finish_reason 及代码/返回均保存，API key 不写入这些文件。

```bash
# 已冻结，不能再次 prepare 或覆盖；模型采集仅补未完成记录
python experiments/experiment_a.py run --output data/ours/experiment_a/20261108 --workers 4
# 不会调用模型；未齐时只出进度与明确标记的 common-cell sensitivity
python experiments/report_experiment_a.py --output data/ours/experiment_a/20261108
```

密钥从 GEMINI_API_KEY 环境变量或隐藏输入进入内存。CPU 子进程不继承密钥环境。恢复须保持相同代码/请求哈希，不能为提分重跑 completed invalid/refusal/truncated。网络认证/配置/隔离失败或持续 transport failure 会停止；保留故障，不将未完成当作拒绝。并发可按注册修订减到2或1。

采集期间仅监控完成数、接口错误和请求用量；810 齐后执行最终主分析。部分结果有明确 interim 标记，不能当作主效应定论。HTTP in-flight 中断可能导致 provider outcome 未知，计账保留该状态。

## 能支持的结论

该试验检验完整 check-aid 包是否改善所选查询上的审计行为，以及可见行代码访问的表现；不是新的总体表样本、三组等算力比较、runtime 放置位置必要性、内部核验意愿或端到端恢复收益检验。没有 generic-warning 组，不能隔离警告措辞与数值检查各自的机制。对应详细设计与出处见 REVIEW_REFRAME_2026-11-08.md 和 PREREGISTRATION.md。

## 采集期间的独立冻结核验

只读 reviewer 重建了每表前五个查询、90 组种子/行索引/展示 CSV，确认30/90/810、六个代码来源及六表 SHA 均与输入冻结提交0a8877b一致；未查看主实验回复或计算中期效果。八项合成/报告测试独立通过。其受限工具环境无法再安装嵌套 Seatbelt，不能将该次实沙箱测试表述为通过；实际隔离证据来自主会话此前的 escalated 九项测试和真实模型工程 smoke 中的两次执行。

正式三组的反事实解释应保持有限：B-A 测整个辅助包；C 的改进与可执行计算相容，但不证明原模型没有核验意愿；B 的 discrimination 改进如伴随 clean 损失，须报告取舍，不能用减少回答掩盖错误。是否满足联合规则只在完整810条的冻结分析中判定。

## 已披露的中途工具修复

扩展的合成 NumPy bootstrap 检查发现，初版导入钩子拒绝库内部的 numpy.core._methods。暂停时554条轨迹已完成；全部按原字节和SHA保留，没有按得分重跑。修订5101177记录原因与分析边界，runtime_patch_1.json绑定旧/新程序哈希及554个原回复。原始manifest/config不变，新调用有runtime_segments和phase2配置。修复后的真实seeded/unseeded NumPy bootstrap与源文件读取拒绝回归通过；继续的只是256个未完成单元。

raw/check无该Python工具，注册的B-A主分析保持。C跨两个实现阶段，整组对照只作诊断，不能作为均一的计算对照或模型计算能力证据；报告按阶段的工具错误。只读独立核验确认554文件、旧/新指纹、原始输入和提示/请求常量不变，未查看主实验决策或计算中期效果。此修复没有增加模型样本，也不授权重生完成的C输出。

续跑必须显式传入 `--runtime-patch data/ours/experiment_a/20261108/runtime_patch_1.json`，不能绕开代码哈希检查。
