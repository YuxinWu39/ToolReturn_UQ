# 论文与排版状态（2026-11-08，revision 4）

英文主稿：[manuscript.md](manuscript.md)。本轮按 [更新后复核](../docs/REVIEW_UPDATED_PAPER_2026-11-08.md) 修订摘要、结果、系统启示及结论；已包含 Gemini 实验 A 和 Qwen3-8B raw/check 复现，旧 12 查询 pilot 位于附录。

当前结论：Qwen 在 fired 轨迹中的错误采纳率为 97–99%；Gemini 为 56%，但其输出单位不同，不能据此排名。指定 bootstrap 检查的 AUROC 随随机可见行预算增加而上升。实验 A 的 check 信息包改善两模型的接受区分度，但 Qwen 同时损失正确值接受率，未通过注册联合规则。Gemini 能救回误标的正确值，也放过更多被标记的错误值；模型参与改变了误伤与漏检的权衡。探索性的 flag-only 对照没有显示 aided 模型更高的观察区分度，也没有证明等价。Runtime 服务是待验证设计方向，尚未测部署收益或长期演化。

## 文件与复现

- `manuscript.md`：完整英文稿。十一张生成表由 `experiments/export_paper_evidence.py` 管理，不能手改生成区段。
- `evidence.json`：28 项证据、16 个输入文件哈希与来源 JSON pointer；不等于全部叙述已经自动验证。
- `references.bib`：方法、近邻工作及源数据的参考文献。开发辅助资源保留在内部记录，排版稿不把它当作实证贡献。
- `build_submission.py`：从英文稿及生成表构建匿名 LaTeX，检查派生源文件漂移；正文和附录不重新估计结果。
- `submission.tex`、`aaai2027.sty`、`aaai2027.bst`：排版源文件及未经修改的官方样式。
- `output/pdf/submission.pdf`：编译后的匿名稿；共五页；正文和核心表在前四页，检查结果见 `SUBMISSION_CHECKS.md`。

在仓库根目录运行：

```bash
python experiments/export_paper_evidence.py --check
python paper/build_submission.py --check
# 安装 pdfLaTeX/BibTeX 后：
python paper/build_submission.py --compile
```

本轮是证据范围修订和格式转换，无新估计、模型请求或补样。数值主张来自现有保存结果；保留原始数据、旧评审及历史 findings。Qwen 的 540 条和 Gemini 的 810 条原始记录齐全；Gemini code arm 跨运行时版本，只用于诊断。

## 场馆要求与仍需作者处理的事项

[官方 workshop 征稿](https://trust4rsi-agent.github.io/AAAI2027/)列出 2026-11-20 AoE 截止、四页短文/八页全文、AAAI 2027 格式、双盲及 non-archival。参考文献和附录通常不计页数，最终仍以投稿页面为准。本稿按四页正文准备。

匿名稿不包含作者、个人仓库链接或本机路径。尚未创建或发布外部匿名 artifact；正文使用中性的数据可用性说明，不虚构匿名链接。投稿前需由作者确认署名和 AI 辅助披露、准备可供评审访问的匿名复现材料，并在 OpenReview 上传。此次工作不执行公开发布或投稿。

修订内容和格式/匿名性核验记录见 `SUBMISSION_CHECKS.md`。原正式五席评审的状态不会因本轮写作自动改成通过。
