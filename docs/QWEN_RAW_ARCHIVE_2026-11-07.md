# Qwen 原始回复归档核验（2026-11-07）

`git pull --rebase origin main` 已成功，没有冲突。远端 `e9e3577` 新增 72 条 Qwen 原始回复，本地三个修订提交完整重放在其后；重放前曾保留临时备份分支，核对三个提交内容等价后已按用户要求删除；当前工作仍在 main。仓库自己的 `pull.rebase=true` 已设置，未修改全局 Git 配置。

## 核验结果

- 原始文件 72/72，恰好覆盖冻结 manifest 的全部单元；无缺失或多余单元。
- manifest、messages 和实际请求 payload 哈希一致；raw、严格解析后的 parsed、原 scored_responses 一致。
- provider content、模型名、finish_reason、usage 与归档字段及评分记录一致；观测到 `qwen3-8b` 和 `vllm-0.31.0-a5cbd462` 指纹。这不是模型权重哈希或提供方独立证明。
- 在临时目录用原 summarize 函数从 72 条 raw 重建，完整 summary.json 和 scored_responses.json 与已保存版本逐字段一致；没有覆写原文件。
- 既有行为主对照仍为 0.000，表 bootstrap 区间 [−0.333, 0.333]；三种 context 下错误接受数分别为 head5 10/12、random20 9/12、matched20 11/12。归档补齐没有改变实验结论。

机器可读记录：[raw_archive_audit.json](../data/ours/context_pilot/20261107/raw_archive_audit.json)，包含两模型逐条原文件 SHA-256 和核验结果。使用以下命令复核请求/回复/评分/行为主对照，不会调用模型：

```bash
python experiments/audit_context_replication.py --output /tmp/toolreturn-archive-verification.json
```

## 当前限制与历史记录

“Qwen 原始回复缺档”已解除，当前 README、研究状态、结论和作者回应同步更新。旧五席审稿、旧审计和 append-only 日志保留其当时快照，不回写历史。

仍只有 12 查询、6 表，每条件一次回答；缺少 live 极端污染 sanity，因此 confidence AUROC 继续 withheld。归档完整不等于假设确认、模型等效或论文已被接受。此次没有新模型调用。

Rebase 提交映射：`89361ee → ce7d907`（原审稿），`27ab078 → e7f319d`（审计协议），`b4d3ef9 → d985a00`（作者修订）。原审稿/历史文件中的旧哈希保留为重放前出处，当前文档和状态使用新哈希。
