#!/usr/bin/env python3
"""Generate the independent-draw report and finding from saved summaries."""
import argparse
import json
from pathlib import Path


def render(s):
    x=s['methods']['0d'];a,b=x['policy']['clean'],x['policy']['corrupted']
    lines=['# 独立抽样稳健性检查（2026-11-07）','','## 结论', '',
           '在这十二个选定查询上，二十条相关样本包含统计方法可利用的判别信号，但效果依赖任务和抽样。该结果支持继续检验证据如何被模型使用，不证明某个模型内部机制。', '',
           f"每查询二十次新抽样，共 {s['query_draw_units']} 个 query/draw 单位；仍然只有十二个查询、六张表，不是新增 240 个独立任务。每次筛选后均匀抽取二十个有效值，单次不放回，跨次允许重叠。", '',
           '| 方法 | 错误返回被标出 | 正确返回被误标 | Sanity AUROC | 真实污染表内 AUROC | 描述性区间 |',
           '|---|---:|---:|---:|---:|---|']
    for method,z in s['methods'].items():
        aa,bb=z['policy']['clean'],z['policy']['corrupted'];v=z['detection']
        lines.append(f"| {method} | {bb['flag']}/{bb['n']} | {aa['flag']}/{aa['n']} | {z['sanity']['within_table']:.3f} | {v['within_table']:.3f} | [{v['ci95'][0]:.3f}, {v['ci95'][1]:.3f}] |")
    lines += ['',f"主方法 0d：错误检出率 {100*b['flag']/b['n']:.1f}%，正确值误标率 {100*a['flag']/a['n']:.1f}%。仍有 {b['compatible']}/{b['n']} 个错误值与样本区间相容。", '',
              '0a 为样本范围检查，0d 为既有 bootstrap 均值区间检查。两者通过预设 sanity；通过不等于已校准。', '',
              '| 0d 指标 | 六表等权比例 | 六表描述性 bootstrap 区间 |','|---|---:|---|']
    for role,z in x['flag_rates'].items():
        lines.append(f"| {role} flag rate | {100*z['mean']:.1f}% | [{100*z['ci95'][0]:.1f}%, {100*z['ci95'][1]:.1f}%] |")
    lines += ['', '区间按六张表聚类，不把 240 次抽样当独立表。区间描述选定表/查询上的变异，不是有限总体误报保证。0a 的零误报及退化区间 [0,0] 来自全零观察；0d 的实测比例也不证明已达到 5% 校准。', '',
              '## 严重度切片', '', '| 方法 | 切片 | 错误标出 | 正确误标 | 表内 AUROC |', '|---|---|---:|---:|---:|']
    for method,z in s['methods'].items():
        for sev,v in z['per_severity'].items():
            aa,bb=v['policy']['clean'],v['policy']['corrupted']
            lines.append(f"| {method} | {sev} | {bb['flag']}/{bb['n']} | {aa['flag']}/{aa['n']} | {v['detection']['within_table']:.3f} |")
    lines += ['', 'subtle 使用 1.10 倍或倒数，plausible 使用 1.50 倍或倒数，但切片绑定不同查询。差异不能全归因于扰动幅度；下一轮应在每个查询内部交叉严重度。', '',
              '## 每个原查询的抽样敏感性', '', '| 查询 | 0d 错误标出 / 20 | 0d 正确误标 / 20 |', '|---|---:|---:|']
    for task,z in x['per_query'].items():
        lines.append(f"| {task} | {z['corrupted']['flag']}/{z['corrupted']['n']} | {z['clean']['flag']}/{z['clean']['n']} |")
    lines += ['', '查询间差异明显，不能用平均值覆盖低检出任务。此次无缺失评分。', '',
              '## 与前轮结果的关系', '',
              '原冻结样本 0d AUROC 为 0.917；本轮查询/抽样混合分布约为 0.818。估计对象不同，可以并列，不能据此证明最初幸运、有偏，或正式量化性能下降。两份数据和报告均保留。', '',
              '前轮相同样本对照支持存在统计方法与模型判断的差距。本轮只检查统计核验的抽样敏感性；没有让 Gemini/Qwen 读取新样本，没有复用旧回答。因此不能声称模型差距在这些新 draw 上复现，也没有排除旧模型试验的公开数据集先验、格式或 confidence 问题。', '',
              '## 论文现在能说什么', '',
              '1. 在已测协议下，直接增加相关样本尚未带来跨模型稳定核验收益。',
              '2. 这些选定查询的相关样本含有程序化统计核验可利用的信号；抽样重复后仍可观察到，具体任务和抽样影响效果，轻微扰动切片仍难。',
              '3. 证据可用性与核验程序的证据利用应分别评价。“信息不足”不能概括全部失败，但尚未定位模型内部原因或提出新算法。', '',
              '投稿判断：值得组织成实证 workshop 短文，但无法给可靠录用概率。目标 workshop 接受负结果与四页短文。应定位为运行时工具返回核验的实证研究，说明与系统审计的联系；当前没有测试长期可信演化。'
              '[官方征稿](https://trust4rsi-agent.github.io/AAAI2027/)', '',
              '## 下一轮实验', '',
              '在新生成或数值变换的表上，比较原始样本行与由同一批行计算的统计摘要。保留直接 0d 基线、clean、极端错误 sanity、弃答和格式计数；每查询内部交叉扰动幅度。摘要只给样本均值、样本量和区间等可验证量，不夹带总体真值或正确标签。', '',
              '先锁定生成、随机化和评分。考虑摘要长度、提示和计算预算变化的控制。这测的是证据表达/计算辅助的干预效果，不能直接等同模型内部机制。新表/任务泛化与新算法优势均未建立；本阶段固定完成，不补挑抽样。', '',
              '## 复现与审查', '',
              f"协议 `{s['audit']['protocol_commit']}`，代码 `0494e7f`，清单冻结 `b192a58`。{s['events']} 个事件、240 组可见样本；仍为六表、十二个查询。复用 B=2000 与原统计实现，没有修改 zeroparam.py。", '',
              '两项新增测试、前阶段九项 synthetic 检查及共享 helpers 三组检查通过。独立 reviewer 从保存区间/范围复算全部 score，并用分数逐对排序核对 AUROC，未重跑 bootstrap；PASS-AS-EXPLORATORY。', '',
              '```bash','python experiments/report_context_resampling.py','```', '',
              '设计与审查使用 experimental-design / scientific-critical-thinking skills。方法资源：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. [arXiv:2609.00065](https://doi.org/10.48550/arXiv.2609.00065)。','']
    return '\n'.join(lines)


def finding(s):
    x=s['methods']['0d'];a,b=x['policy']['clean'],x['policy']['corrupted'];d=x['detection']
    lines=['','','## F12 — Independent row-draw robustness, selected queries (2026-11-07, exploratory)','',
           'A-CTX-RESAMPLE protocol 7f6400e, code 0494e7f, evidence freeze b192a58. Twenty new matched20 draws per each of twelve original queries: 240 query/draw units, still six tables. No new LLM replies or reuse of old replies on new rows.','',
           f"0d sanity {x['sanity']['within_table']:.6f} passes. Query/draw-mixture within-table AUROC {d['within_table']:.6f}, descriptive six-table CI [{d['ci95'][0]:.6f}, {d['ci95'][1]:.6f}]. Flags {b['flag']}/{b['n']} corruptions ({100*b['flag']/b['n']:.1f}%) and {a['flag']}/{a['n']} clean values ({100*a['flag']/a['n']:.1f}%); no missing scores. Observed rates are not calibration guarantees.",'',
           '| 0d slice | Corrupted flags | Clean false flags |','|---|---:|---:|']
    for sev,v in x['per_severity'].items():
        lines.append(f"| {sev} | {v['policy']['corrupted']['flag']}/{v['policy']['corrupted']['n']} | {v['policy']['clean']['flag']}/{v['policy']['clean']['n']} |")
    lines += ['',f"Severity is tied to query. Secondary 0a passes sanity, real AUROC {s['methods']['0a']['detection']['within_table']:.6f}; zero observed clean flags are not a zero-population-error guarantee.",'',
              'Signal persists across sampling for these selected queries, with task heterogeneity and missed subtle cases. Single-draw 0.917 and mixture 0.818 estimate different targets; their difference does not prove initial luck/bias. No new table/task generalization, model-gap replication, identified internal mechanism or new algorithm. Independent artifact/ranking review: PASS-AS-EXPLORATORY.','',
              'Next: preregister fresh-table raw-rows versus same-row-statistics controls, crossing severity within each query and retaining 0d/clean/sanity. [Generated report](docs/CONTEXT_EVIDENCE_RESAMPLING_2026-11-07.md).','']
    return '\n'.join(lines)


if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=root);p.add_argument('--report',type=Path);p.add_argument('--finding',type=Path)
    a=p.parse_args();s=json.loads((a.root/'data/ours/context_evidence_resample/20261107/summary.json').read_text())
    target=a.report or a.root/'docs/CONTEXT_EVIDENCE_RESAMPLING_2026-11-07.md'
    target.write_text(render(s))
    if a.finding:a.finding.write_text(finding(s))
    print(target)
