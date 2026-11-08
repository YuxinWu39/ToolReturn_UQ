#!/usr/bin/env python3
"""Deterministic Markdown-to-AAAI submission export; no estimates or model calls.

Run from any directory: python paper/build_submission.py [--check].
Compile with --compile and pdfLaTeX/BibTeX; see SUBMISSION_CHECKS.md.
"""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent


def escape(s):
    chars = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$',
             '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}',
             '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}
    unicode = {'×': r'\(\times\)', '÷': r'\(\div\)', '→': r'\(\rightarrow\)',
               '−': '-', '–': '--', '—': '---', '≥': r'\(\geq\)',
               '≤': r'\(\leq\)', '∈': r'\(\in\)', '±': r'\(\pm\)', '’': "'", '‘': "'",
               '“': '``', '”': "''"}
    return ''.join(chars.get(c, unicode.get(c, c)) for c in s)


KEYS = {'Tao and Yin, 2026': 'TaoYin2026', 'Yang et al., 2026': 'Overreliance',
        'Kraishan, 2026': 'LoudQuietFailures', 'Panthi and Abdelfattah, 2026': 'OutcomeMonitors',
        'Kekatos et al., 2026': 'FormalRuntimeVerification',
        'Jegatheesan and Lihinikaduarachchi, 2026': 'MathAgentsCorrupted',
        'Xu et al., 2026': 'Xu2026', 'Efron, 1979': 'Efron1979'}


def inline(s):
    protected = []

    def hold(tex):
        key = f'QZX{len(protected)}QXZ'
        protected.append(tex)
        return key

    s = s.replace(r'0o\*', '0o*')
    for name, key in [('Yang et al.', 'Overreliance'), ('Kraishan', 'LoudQuietFailures'),
                      ('Kekatos et al.', 'FormalRuntimeVerification'),
                      ('Jegatheesan and Lihinikaduarachchi', 'MathAgentsCorrupted'),
                      ('Xu et al.', 'Xu2026')]:
        s = s.replace(name + ' [2026]', hold(r'\citet{' + key + '}'))

    def cite(m):
        names = m.group(1).split('; ')
        return hold(r'\citep{' + ','.join(KEYS[n] for n in names) + '}') if all(n in KEYS for n in names) else m[0]

    s = re.sub(r'\[([^\[\]]+)\]', cite, s)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', lambda m: hold(escape(m[1]) + r' (\url{' + m[2] + '})'), s)
    s = re.sub(r'`([^`]+)`', lambda m: hold(r'\path|' + m[1] + '|'), s)
    s = re.sub(r'\*\*([^*]+)\*\*', lambda m: hold(r'\textbf{' + escape(m[1]) + '}'), s)
    s = re.sub(r'(?<!\w)\*([^*]+)\*(?!\w)', lambda m: hold(r'\emph{' + escape(m[1]) + '}'), s)
    s = escape(s)
    for i, tex in enumerate(protected):
        s = s.replace(f'QZX{i}QXZ', tex)
    return s


def parse_table(text):
    return [[c.strip() for c in l.strip().strip('|').split('|')]
            for i, l in enumerate(text.strip().splitlines()) if i != 1]


def tabular(rows, spec, small=True):
    return '\n'.join(([r'{\small'] if small else ['{']) +
                     [r'\setlength{\tabcolsep}{3pt}', r'\begin{tabular}{' + spec + '}', r'\toprule'] +
                     [' & '.join(inline(c) for c in row) + r' \\' + (r' \midrule' if i == 0 else '') for i, row in enumerate(rows)] +
                     [r'\bottomrule', r'\end{tabular}', '}'])


def table(name, data, caption):
    rows = parse_table(data)
    cap = re.sub(r'^\*\*Table \d+\.\*\*\s*', '', caption)
    wide = True
    extra = ''
    if name == 'adoption':
        rows[0] = ['Agent / tier', 'Fired', 'Used', 'Rows seen: used', 'No rows: used']
        rows = [rows[0]] + [[r[0].replace('qwen3-', 'Qwen3-').replace('4b', '4B').replace('8b', '8B').replace('gemini-3.8-flash', 'Gemini Flash') + ' / ' + r[1].replace('T0_agent', 'T0'), *r[2:]] for r in rows[1:]]
        spec = 'lrrrr'
    elif name == 'ksweep':
        wide = False
        rows = [['k', '0d', '0o*', '0o', 'Sanity min.']] + [
            [rows[0][i].replace('k=', '')] + [rows[j][i] for j in range(1, 5)] for i in range(1, 7)]
        spec = 'rrrrr'
        cap = cap.replace('sanity row', 'sanity column').replace('privileged rows', 'privileged columns')
        cap += ' 0d uses visible rows.'
    elif name == 'monitor':
        rows[0] = ['Decision maker', 'Clean', '×1.10', '×1.50', 'Change vs rows only [95%]']
        for r in rows[1:]:
            r[0] = r[0].replace('gemini-3.8-flash', 'Gemini Flash').replace('qwen3-8b', 'Qwen3-8B')
            r[4] = r[4].replace(' vs raw', '')
        rows[-1][-1] = 'policy reference'
        spec = 'lrrrl'
    elif name == 'flagonly':
        rows[0] = ['Model', 'Check minus flag [95%]', 'Flagged: accept', 'Unflagged: reject']
        for r in rows[1:]:
            r[0] = r[0].replace('gemini-3.8-flash', 'Gemini Flash').replace('qwen3-8b', 'Qwen3-8B')
        return tabular(rows, 'llrr')
    elif name == 'contrasts':
        wide = False
        rows = [['Model', 'Change [95%]', 'q / t']] + [
            [r[0].replace('gemini-3.8-flash', 'Gemini').replace('qwen3-8b', 'Qwen3-8B'), r[1] + ' ' + r[2], r[3]] for r in rows[1:]]
        spec = 'llr'
    elif name == 'statistics':
        wide = False
        original = rows
        labels = ['Original / 0a', 'Original / 0d', 'Draws / 0a', 'Draws / 0d']
        rows = [['Evidence / check', 'Sanity', 'AUROC [95%]']] + [[label, r[2], r[3]] for label, r in zip(labels, original[1:])]
        spec = 'lll'
        secondary = [['Evidence / check', 'Pooled', 'Corrupt flags', 'Clean flags']] + [
            [label, r[4], r[5], r[6]] for label, r in zip(labels, original[1:])]
        extra = '\n' + r'\par\medskip' + '\n' + tabular(secondary, 'llrr')
        assert all(r[7] == '0 / 0' for r in original[1:])
        cap += ' No clean or corrupted packet is unscorable. Original denotes matched20; draws denotes twenty draws per query.'
    elif name == 'pilot':
        wide = False
        rows[0] = ['Model', 'Context', 'Clean', 'Corrupt', 'U', 'I']
        for r in rows[1:]:
            r[0] = r[0].replace('gemini-3.8-flash', 'Gemini').replace('qwen3-8b', 'Qwen3-8B')
        spec = 'llrrrr'
        cap += ' Acceptances are out of twelve per type. U and I denote uncertain and invalid (clean / corrupted).'
    elif name == 'gates':
        wide = False
        rows[0] = ['Context', 'Check', 'Sanity', 'q / t', 'Efficacy']
        spec = 'llrrl'
        cap += ' q / t is the number of paired queries / tables for sanity.'
    elif name == 'severity':
        wide = False
        rows = [['Check / slice', 'Corrupt', 'Clean', 'AUROC [95%]']] + [
            [r[0] + ' / ' + r[1], r[2], r[3], r[4]] for r in rows[1:]]
        spec = 'lrrl'
        cap += ' Corrupt and Clean are flag counts.'
    elif name == 'scorer':
        wide = False
        assert all(r[2] == 'fail' and r[4] == 'withheld-scorer-gate-failed' for r in rows[1:])
        rows = [['Configuration', 'Coverage', 'P+S q / t']] + [[
            r[0].replace('qwen3-4b_', 'Qwen3-4B / ').replace('qwen3-8b_', 'Qwen3-8B / ').replace('T0_agent', 'T0'), r[1], r[3]] for r in rows[1:]]
        spec = 'lrr'
        cap += ' All real-corruption gains are withheld. P+S q / t is the common plausible-plus-subtle query / table count.'
    elif name == 'datasets':
        wide = False
        rows = [['Export / rows / license', 'Source / SHA-256 prefix']] + [[
            r[0] + ' / ' + r[1] + ' / ' + r[2],
            re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', r[3]) + ' / ' + r[4]] for r in rows[1:]]
        spec = r'>{\raggedright\arraybackslash}p{1.59in}>{\raggedright\arraybackslash}p{1.53in}'
    else:
        raise ValueError(f'Unknown generated table: {name}')
    env = 'table*' if wide else 'table'
    return '\n'.join([r'\begin{' + env + '}[tbp]', r'\centering', tabular(rows, spec), extra,
                      r'\caption{' + inline(cap) + '}', r'\label{tab:' + name + '}', r'\end{' + env + '}'])


def generate():
    source = (ROOT / 'manuscript.md').read_text()
    title = source.splitlines()[0][2:]
    abstract = source.split('## Abstract\n\n')[1].split('\n\n## 1.')[0]
    body = source.split('## 1. Introduction\n\n', 1)[1]
    body = '## 1. Introduction\n\n' + body
    # Bibliography is rendered from BibTeX, not a duplicated manually formatted list.
    body = re.sub(r'## References\n.*?(?=## Appendix A\.)', 'QZXREFERENCESQXZ\n\n', body, flags=re.S)
    blocks = re.split(r'(<!-- BEGIN GENERATED:\w+ -->.*?<!-- END GENERATED:\w+ -->)', body, flags=re.S)
    out = []
    for idx, block in enumerate(blocks):
        if block.startswith('<!-- BEGIN GENERATED:'):
            m = re.fullmatch(r'<!-- BEGIN GENERATED:(\w+) -->\n(.*?)\n<!-- END GENERATED:\w+ -->', block, re.S)
            name, data = m.groups()
            next_text = blocks[idx+1] if idx+1 < len(blocks) else ''
            match = re.match(r'\s*(\*\*Table \d+\.\*\*[^\n]+)', next_text)
            cap = match[1] if match else {
                'contrasts': 'Earlier pilot: matched20 minus random20 acceptance discrimination.',
                'statistics': 'Fixed-return pilot and row-draw audit: gate-eligible statistical results.',
                'pilot': 'Earlier pilot decisions, with all failures retained.',
                'gates': 'Sanity gates by evidence context; failed gates withhold efficacy.',
                'severity': 'Severity slices from the row-draw audit; queries differ between slices.',
                'scorer': 'Cached learned scorers: all configurations fail eligibility gates.',
                'datasets': 'Versioned CSV datasets and provenance. SHA-256 prefixes identify the saved exports.',
            }.get(name, '')
            if match:
                blocks[idx+1] = next_text[match.end():]
            if name == 'monitor':
                # Combine the two Table 3 panels; never shrink a wide table.
                following = blocks[idx+2]
                fm = re.search(r'<!-- BEGIN GENERATED:flagonly -->\n(.*?)\n<!-- END GENERATED:flagonly -->', following, re.S)
                assert fm
                caption_text = re.match(r'\s*(\*\*Table 3\.\*\*[^\n]+)', blocks[idx+3])[1]
                blocks[idx+3] = blocks[idx+3].replace(caption_text, '', 1)
                top = table(name, data, caption_text)
                insert = '\n' + r'\par\medskip' + '\n' + table('flagonly', fm[1], '')
                top = top.replace(r'\caption{', insert + '\n' + r'\caption{', 1)
                # Direct-minus-raw contrasts remain in the complete Markdown evidence table;
                # the compact PDF displays the acceptance counts and check-minus-flag contrasts.
                out.append(top)
            elif name != 'flagonly':
                out.append(table(name, data, cap))
            continue
        lines = block.strip().splitlines()
        paragraph = []
        in_list = False

        def flush():
            if paragraph:
                out.append(inline(' '.join(paragraph)) + '\n')
                paragraph.clear()

        for line in lines + ['']:
            if not line.strip():
                flush()
                if in_list:
                    out.append(r'\end{itemize}')
                    in_list = False
            elif line == 'QZXREFERENCESQXZ':
                flush()
                out.extend([r'\nocite{Horst2020,Quinlan1993,Fanaee2013,Nash1994,Cortez2009,Cortez2008}', r'\bibliography{references}', r'\FloatBarrier', r'\appendix'])
            elif line.startswith('##'):
                flush()
                level, text = line.split(' ', 1)
                text = re.sub(r'^\d+(?:\.\d+)*\.?\s+', '', text)
                if text.startswith('Appendix '):
                    text = text.split('. ', 1)[1]
                out.append('\\' + ('subsection' if level == '###' else 'section') + '{' + inline(text) + '}')
            elif re.match(r'^(?:\d+\.|-) ', line):
                flush()
                if not in_list:
                    out.append(r'\begin{itemize}')
                    in_list = True
                out.append(r'\item ' + inline(re.sub(r'^(?:\d+\.|-) ', '', line)))
            else:
                paragraph.append(line)
    preamble = r'''% Generated by build_submission.py from manuscript.md; edit that source.
\documentclass[letterpaper]{article}
\usepackage[submission]{aaai2027}
\usepackage[hyphens]{url}
\usepackage{graphicx}
\urlstyle{rm}
\def\UrlFont{\rm}
\usepackage{natbib}
\usepackage{caption}
\usepackage{booktabs}
\usepackage{array}
\frenchspacing
\pdfinfo{/TemplateVersion (2027.1)}
\setcounter{secnumdepth}{2}
'''
    return preamble + '\\title{' + inline(title) + '}\n' + r'\author{Anonymous Authors}' + '\n' + r'\affiliations{}' + '\n' + r'\begin{document}' + '\n' + r'\maketitle' + '\n' + r'\begin{abstract}' + '\n' + inline(abstract) + '\n' + r'\end{abstract}' + '\n' + '\n\n'.join(out) + '\n' + r'\end{document}' + '\n'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check', action='store_true')
    p.add_argument('--compile', action='store_true', help='compile PDF with pdfLaTeX and BibTeX')
    p.add_argument('--tex-bin', type=Path, help='directory containing pdflatex and bibtex (otherwise PATH)')
    a = p.parse_args()
    content = generate()
    target = ROOT / 'submission.tex'
    if a.check:
        if not target.exists() or target.read_text() != content:
            raise SystemExit('Submission source drift: run python paper/build_submission.py')
        print('PASS: submission.tex matches manuscript and table formatting rules')
    else:
        target.write_text(content)
        print('Generated submission.tex; no new estimates or model requests')
    if a.compile:
        tools = {name: str(a.tex_bin / name) if a.tex_bin else shutil.which(name) for name in ('pdflatex', 'bibtex')}
        if any(not path or not Path(path).is_file() for path in tools.values()):
            raise SystemExit('pdfLaTeX and BibTeX are required; install TeX Live/TinyTeX or pass --tex-bin')
        folder = ROOT / 'output' / 'pdf'
        folder.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env.update(BIBINPUTS=str(ROOT) + ':', BSTINPUTS=str(ROOT) + ':')
        with tempfile.TemporaryDirectory(prefix='toolreturn-tex-') as temporary:
            latex = [tools['pdflatex'], '-interaction=nonstopmode', '-halt-on-error', '-output-directory=' + temporary, 'submission.tex']
            sequence = [(latex, ROOT), ([tools['bibtex'], 'submission'], Path(temporary)), (latex, ROOT), (latex, ROOT)]
            for command, cwd in sequence:
                result = subprocess.run(command, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                if result.returncode:
                    raise SystemExit(result.stdout[-6000:])
            log = (Path(temporary) / 'submission.log').read_text(errors='replace')
            if any(token in log for token in ('Overfull \\hbox', 'Overfull \\vbox', 'Missing character:', 'There were undefined citations')):
                raise SystemExit('Compilation has overflow, missing glyphs or unresolved citations:\n' + log[-6000:])
            shutil.copy2(Path(temporary) / 'submission.pdf', folder / 'submission.pdf')
        print('Compiled output/pdf/submission.pdf; no overflow or missing-citation warnings')


if __name__ == '__main__':
    main()
