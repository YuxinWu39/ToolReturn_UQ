#!/usr/bin/env python3
"""Render A-CTX-EVIDENCE artifacts and report from the saved run, without rerunning it."""
import argparse
import hashlib
import json
import os
from pathlib import Path


def fmt(x):
    return 'withheld' if x is None else f'{x:.3f}'


def finding(s):
    x=s['methods']['0d']['matched20'];a,b=x['policy']['clean'],x['policy']['corrupted'];d=x['detection']
    q=x['model_comparison']['qwen3-8b']['all_model_formats']['common_support_decisions']
    g=x['model_comparison']['gemini-3.8-flash']['all_model_formats']['common_support_decisions']
    return f'''

## F11 — Same-evidence statistical feasibility (2026-11-07, exploratory)

A-CTX-EVIDENCE protocol `{s['audit']['protocol_commit']}`, frozen analysis code `{s['audit']['code_commit'][:7]}`.
No new LLM calls. Existing twelve filtered-mean queries, six tables, one frozen sample per
query/context; features parsed only from the exact CSV evidence shown to models.

Primary 0d matched20 passes sanity AUROC {x['sanity']['within_table']:.3f}, with
{d['paired_queries']} paired queries/{d['tables']} tables. Actual within-table AUROC
{d['within_table']:.3f}, descriptive six-table bootstrap CI [{d['ci95'][0]:.3f}, {d['ci95'][1]:.3f}];
pooled AUROC {d['pooled']:.3f} is secondary. Fixed compatibility policy flags
{b['flag']}/{b['n']} corrupted returns and {a['flag']}/{a['n']} clean returns;
{b['compatible']}/{b['n']} corruptions remain compatible. No unscorable matched20 cases.

On the identical matched20 data evidence, Qwen accepts {q['corrupted']['model']['accept']}/{b['n']} corrupted returns and
{q['clean']['model']['accept']}/{a['n']} clean returns; Gemini accepts {g['corrupted']['model']['accept']}/{b['n']} corrupted and {g['clean']['model']['accept']}/{a['n']} clean, with {g['corrupted']['model']['invalid']} corrupted and
{g['clean']['model']['invalid']} clean invalid response(s). These are prompted model judgments versus a structured-query
statistical procedure, not equivalent representations, computation, cost, or calibrated
probabilities. Gemini valid-pair sensitivity has only nine queries/five tables. No claim
of generally superior model performance or identified internal mechanism.

0a matched20 passes sanity but has actual within-table AUROC
{s['methods']['0a']['matched20']['detection']['within_table']:.3f}. Both methods at head5/random20
fail sanity; their real AUROCs and all cross-context policy contrasts are withheld, not
used as evidence of a quantified context benefit. Counts for failed conditions remain
gate-failed diagnostics. Bootstrap intervals have no asserted finite-population 95% guarantee.

Interpretation: this fixed matched20 sample contains statistical signal accessible to an
existing checker. Insufficient displayed data alone cannot summarize all model failures
here. Extraction/representation/use of evidence are candidates for a fresh intervention,
not proven mechanisms. Selected reused tasks, six clusters, one sample/completion, public
data priors and missing Qwen raw responses limit scope. No new algorithm or universal bound.
Independent event/formula/ranking review: PASS-AS-EXPLORATORY.

Next: independent row-draw robustness and fresh generated/transformed-table controls, then
raw rows versus summaries derived from the identical rows, retaining 0d, clean and sanity
controls. Each new study gets its own protocol; no outcome-driven expansion of this run.
Full generated tables, plot, exceptions and paper implications:
[report](docs/CONTEXT_EVIDENCE_2026-11-07.md).
'''


def report(s,features,events,models):
    x=s['methods']['0d']['matched20'];d=x['detection']
    out=['# 相同样本的统计核验实验（2026-11-07）','','## 这轮回答了什么','','在本轮十二个预选查询的相关二十行条件中，已有 bootstrap 核验器能提取出明显判别信号，而提示式模型审计仍接受较多错误返回。因而，单纯“展示的数据太少”不足以概括这些模型失败；证据提取、表示和使用过程值得进一步干预检验。','','这不是新算法；也没有证明某个内部机制或统计方法普遍优于 LLM。数值证据相同，但统计程序拿到明确的结构化查询规格，并执行了 bootstrap 运算；两者的输入表示、计算过程和成本不相同。','','## 主要结果：相同的相关 20 行','','| 核验方式 | 保留正确返回 | 接受/兼容错误返回 | 明确标错/拒绝错误 | 不确定错误 | 正确 / 错误格式失败 |','|---|---:|---:|---:|---:|---|']
    a,b=x['policy']['clean'],x['policy']['corrupted']
    out.append(f"| bootstrap 0d | {a['compatible']}/{a['n']} | {b['compatible']}/{b['n']} | {b['flag']}/{b['n']} | 0 | 0 / 0 |")
    for name,rows in models.items():
        clean=[r for r in rows if r['context']=='matched20' and r['label']==0]
        toxic=[r for r in rows if r['context']=='matched20' and r['label']==1]
        n=lambda rows,decision:sum(r['decision']==decision for r in rows)
        out.append(f"| {name} | {n(clean,'accept')}/{len(clean)} | {n(toxic,'accept')}/{len(toxic)} | "
                   f"{n(toxic,'reject')}/{len(toxic)} | {n(toxic,'uncertain')} | {n(clean,'invalid')} / {n(toxic,'invalid')} |")
    out += ['',f"0d 通过极端污染 sanity（AUROC={x['sanity']['within_table']:.3f}）。真实污染的表内 AUROC={d['within_table']:.3f}，"
            f"六表描述性 bootstrap 区间 [{d['ci95'][0]:.3f}, {d['ci95'][1]:.3f}]；pooled={d['pooled']:.3f}，仅作次要结果。",
            '',f"固定规则下，0d 标出错误 {b['flag']}/{b['n']}，同时误标正确 {a['flag']}/{a['n']}。"
            '“兼容”只表示没有与样本统计冲突，不能当成“已经确认正确”。模型不接受可能是拒绝、犹豫或格式失败，应分别看。', '',
            '## 所有条件，包括失败的条件', '',
            '| 方法 | Context | 有分数的查询 / 12 | Sanity AUROC | 正确值被标错 | 错值被标错 | 真实污染表内 AUROC |',
            '|---|---|---:|---:|---:|---:|---|']
    for method in ('0a','0d'):
        for c in ('head5','random20','matched20'):
            z=s['methods'][method][c];aa,bb=z['policy']['clean'],z['policy']['corrupted']
            out.append(f"| {method} | {c} | {aa['n']-aa['unscorable']}/12 | {fmt(z['sanity']['within_table'])} | "
                       f"{aa['flag']}/12 | {bb['flag']}/12 | {fmt(z['detection']['within_table'])} |")
    out += ['','未通过 sanity 的行仅是失败诊断；对应真实 AUROC 和跨 context 效应按协议 withheld。不能用这张表宣称已量化“相关 20 行比随机 20 行更好”。head5 经常没有筛选后的有效样本；缺失没有填成正常分数。','','## 严重度和逐查询例外','','| 0d matched20 严重度 | 错值被标错 | 正确值被误标 | 表内 AUROC |','|---|---:|---:|---:|']
    for sev,z in x['per_severity'].items():
        aa,bb=z['policy']['clean'],z['policy']['corrupted']
        out.append(f"| {sev} | {bb['flag']}/{bb['n']} | {aa['flag']}/{aa['n']} | {fmt(z['detection']['within_table'])} |")
    out += ['','严重度与查询身份绑定，不能把切片差异解释成严重度的因果效果。', '',
            '| 查询 | 样本均值 | 样本 bootstrap 区间 | 正确值判定 | 错误值判定 |',
            '|---|---:|---|---|---|']
    lookup={(e['task_id'],e['role']):e for e in events if e['method']=='0d' and e['context']=='matched20'}
    for f in features:
        if f['context']!='matched20':continue
        lo,hi=f['interval_0d'];a=lookup[(f['task_id'],'clean')];b=lookup[(f['task_id'],'corrupted')]
        out.append(f"| {f['task_id']} | {f['sample_mean']:.5g} | [{lo:.5g}, {hi:.5g}] | {a['decision']} | {b['decision']} |")
    feature_lookup={f['task_id']:f for f in features if f['context']=='matched20'}
    margins=[]
    for e in lookup.values():
        if e['role']=='corrupted' and e['decision']=='flag':
            lo,hi=feature_lookup[e['task_id']]['interval_0d']
            margins.append((max(lo-e['value'],e['value']-hi,0),e['task_id']))
    edge,edge_task=min(margins)
    out += ['','唯一 clean false flag 是 Bike 的 registered / workingday=1；两个未标出的错误是 Abalone Whole_weight 与 Student absences 的 subtle 查询。该例外说明固定样本可能偏离总体，也说明 bootstrap 区间没有自动的 95% 总体覆盖保证。', '',
            f"距离边界最近的已标错返回是 {edge_task}，仅在区间外 {edge:.3g}（原始单位）。当前没有调整阈值；后续独立抽样重复尤其需要检查这种边界判断的稳定性。", '',
            '![Same-evidence interval diagnostic](../data/ours/context_evidence/20261107/intervals_matched20.png)', '',
            '图中数值除以总体真均值，仅为跨量纲绘图。总体真值只用于评价和这条参考线，从未作为核验器特征。每行展示一份冻结样本，不是跨抽样平均。', '',
            '## 与模型的描述性配对差值', '',
            '指标为“兼容正确 − 兼容错误”减去模型“接受正确 − 接受错误”；不是 AUROC 差值。', '',
            '| 模型对照 | 格式处理 | 查询 / 表 | 差值（百分点） | 描述性区间（百分点） |',
            '|---|---|---|---:|---|']
    for name,z in x['model_comparison'].items():
        for k,v in z.items():
            out.append(f"| {name} | {k} | {v['queries']} / {v['tables']} | {100*v['mean']:+.1f} | [{100*v['ci95'][0]:+.1f}, {100*v['ci95'][1]:+.1f}] |")
    out += ['','Gemini 完整有效配对仅九查询、五表，且存在公开数据集先验；Qwen 的原始 responses 尚未入库。该差值不能证明通用模型优劣，也不能定位差距来自提示、算术、表征还是其他内部过程。', '',
            '## 论文结论现在怎么写', '',
            '可写：在选定的数值工具返回任务中，核验表现同时取决于展示的证据和采用的核验程序；直接多展示相关行尚未带来跨模型稳定收益，但相同相关样本中的统计信号能被已有核验器提取。这个结果支持继续研究如何把可核验的证据接入工具返回审计。', '',
            '不可写：所有不确定性方法都没用、模型完全不会利用证据、更多 context 无效、0d 总能识错、0o* 是通用信息论上界、或者已提出一个优于现有方法的新算法。', '',
            '## 投稿判断与下一步', '',
            '有继续组织成实证 workshop 短文的价值，但不能给可靠录用概率。目标 workshop 明确接受负结果与四页短文，同时强调系统机制、审计和可信演化；本项目可定位为运行时工具返回核验的实证研究。当前只测单次数值返回，没有验证长期状态演化，不能包装成已经解决可信演化。'
            '[官方征稿](https://trust4rsi-agent.github.io/AAAI2027/)', '',
            '主要风险仍是六张表、复用的十二个 filtered-mean 查询、一次冻结抽样、两个模型族与既有方法。本轮协议先于新基线测量，但我们已知道任务和模型结果，因此不是独立确认集。', '',
            '下一步先锁定独立抽样重复和新生成/变换表的规则，检查统计核验的误报是否稳定；随后在新表上让 Gemini/Qwen 对照“原始样本行”与“相同行生成的统计摘要”，保留 0d、clean、明显错误 sanity 和弃答计数。摘要不能混入全表真值，只能加工已经展示的样本。这样检验的是可干预的证据表达，而非仅重复比较模型数量。', '',
            '本轮按固定协议到此完成，没有依据效果扩大样本或新调用 API。下一轮需要单独预注册；不能拿扩大后的结果替换这份 pilot。', '',
            '## 实现与审查', '',
            f"- 协议 `{s['audit']['protocol_commit']}`；代码 `{s['audit']['code_commit'][:7]}`；36 个 query/context，288 个 real/sanity/method 事件。",
            '- 0a、0d、区间打分直接复用 zeroparam.py；bootstrap B=2000，按 query/context 独立固定 seed。',
            '- 九项合成数据测试通过；共享 P4 helpers 的三组检查 ALL PASS。',
            '- 独立 reviewer 用保存区间/范围复算全部 score，并用两类分数排序复算 AUROC；没有重跑 bootstrap，未发现新计算错误。',
            '- 统计摘要和图可从 summary/features/events 重新生成；Python/依赖版本、源代码和模型评分文件哈希保存在 config.json。', '',
            '```bash',
            'python experiments/report_context_evidence.py',
            '```', '',
            '设计与审查使用 experimental-design / scientific-critical-thinking skills。方法资源：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. [arXiv:2609.00065](https://doi.org/10.48550/arXiv.2609.00065)。引用用于说明研究辅助工具，不为实验结论背书。','']
    return '\n'.join(out)


def plot_intervals(manifest,features,output):
    os.environ.setdefault('MPLCONFIGDIR','/private/tmp/toolreturn-mpl-config')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    lookup={f['task_id']:f for f in features if f['context']=='matched20'}
    queries=manifest['selected_queries']
    fig,ax=plt.subplots(figsize=(10.6,6.7))
    labels=[]
    short={'public_abalone.csv':'Abalone','public_auto_mpg_v4.csv':'Auto MPG','public_bike_v4.csv':'Bike',
           'public_penguins_v3.csv':'Penguins','public_student.csv':'Student','public_wine_quality.csv':'Wine'}
    for i,q in enumerate(queries):
        f=lookup[q['task_id']];truth=q['truth'];lo,hi=[v/truth for v in f['interval_0d']]
        mu=f['sample_mean']/truth
        ax.plot([lo,hi],[i,i],color='#334155',lw=2.2,label='Visible-sample bootstrap interval' if i==0 else None)
        ax.scatter([mu],[i],color='#334155',s=20,zorder=3,label='Visible-sample mean' if i==0 else None)
        ax.scatter([q['corrupted']/truth],[i],marker='x',s=55,color='#d97706',lw=1.8,zorder=4,
                   label='Corrupted return' if i==0 else None)
        labels.append(f"{short[q['dataset']]}: {q['column']} | {q['filter'][0]}={q['filter'][1]}")
    ax.axvline(1,color='#2563eb',lw=1.4,ls='--',label='Population truth (evaluation only)')
    ax.set_yticks(range(len(queries)),labels=labels,fontsize=8)
    ax.set_ylim(len(queries)-.4,-.7)
    ax.set_xlim(.4,1.65)
    ax.set_xlabel('Value / population truth (normalization for visualization only)',fontsize=9)
    ax.set_title('Fixed query-matched 20-row evidence: bootstrap checks\nExploratory pilot, 12 queries / 6 tables',fontsize=11)
    ax.grid(axis='x',alpha=.2)
    ax.spines[['top','right']].set_visible(False)
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.14),ncol=2,fontsize=8,frameon=False)
    fig.subplots_adjust(left=.40,right=.98,top=.88,bottom=.19)
    for suffix in ('png','pdf'):
        fig.savefig(output/f'intervals_matched20.{suffix}',dpi=180,facecolor='white')
    plt.close(fig)


def main():
    root=Path(__file__).resolve().parents[1]
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=root)
    p.add_argument('--run',type=Path)
    p.add_argument('--report',type=Path)
    p.add_argument('--finding',type=Path)
    p.add_argument('--no-plot',action='store_true')
    a=p.parse_args();root=a.root
    folder=a.run or root/'data/ours/context_evidence/20261107'
    s=json.loads((folder/'summary.json').read_text())
    features=json.loads((folder/'features.json').read_text())
    events=json.loads((folder/'events.json').read_text())
    mf=root/'data/ours/context_pilot/20261107'
    m=json.loads((mf/'manifest.json').read_text())
    assert hashlib.sha256(json.dumps(m,ensure_ascii=False,sort_keys=True,allow_nan=False).encode()).hexdigest()==s['audit']['manifest_hash']
    for name,expected in s['audit']['model_scored_hashes'].items():
        assert hashlib.sha256((mf/name/'scored_responses.json').read_bytes()).hexdigest()==expected
    models={n:json.loads((mf/n/'scored_responses.json').read_text()) for n in ('gemini-3.8-flash','qwen3-8b')}
    target=a.report or root/'docs/CONTEXT_EVIDENCE_2026-11-07.md'
    text=report(s,features,events,models)
    if (root/'data/ours/context_evidence_resample/20261107/summary.json').exists():
        text+='\n\n## 后续独立抽样阶段\n\n随后按单独协议完成二十次独立抽样检查，见 [稳健性报告](CONTEXT_EVIDENCE_RESAMPLING_2026-11-07.md)。两阶段估计对象不同，本报告的原始结果继续保留。\n'
    target.write_text(text)
    if a.finding:a.finding.write_text(finding(s))
    if not a.no_plot:plot_intervals(m,features,folder)
    print(target)


if __name__=='__main__':main()
