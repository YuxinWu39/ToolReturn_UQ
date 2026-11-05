#!/usr/bin/env python3
"""P5 step 3: score P4 events with a C3 ensemble and compare with the zero-parameter references on the same rows.

    python score_scorer.py --members ../../models/scorer/{penguins,automng,...}_s* --eval ../../data/ours/scorer/eval_qwen3-4b_T1.jsonl
    python score_scorer.py --members ../../models/scorer/smoke --eval ... --smoke-eval

LOTO: a member is applied only to events whose table == its holdout_table (meta.json); a member with holdout ""
(none) is applied everywhere (smoke only). Outputs per event: q05..q95 per member, surprise (median over members),
epistemic (std of q50). Reports within-table AUROC + 6-table CI, sanity rows (y*1000, y/1000), clean coverage.
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import roc_auc_score

from train_scorer import QUANTILES, QuantileScorer, load_backbone

HERE = Path(__file__).resolve().parent


def load_member(path, device):
    meta = json.loads((path / "meta.json").read_text())
    tok, bb, _ = load_backbone(meta["model"], lora=False, device=device)
    if (path / "adapter").exists():
        from peft import PeftModel
        bb = PeftModel.from_pretrained(bb, str(path / "adapter"))
    else:
        bb.load_state_dict(torch.load(path / "backbone.pt", map_location="cpu"))
    m = QuantileScorer(bb, bb.config.hidden_size)
    m.head.load_state_dict(torch.load(path / "head.pt", map_location="cpu"))
    return meta, tok, m.to(device).eval()


@torch.no_grad()
def predict(tok, model, texts, device, max_len, batch=16):
    out = []
    for b in range(0, len(texts), batch):
        enc = tok(texts[b:b + batch], padding=True, truncation=True, max_length=max_len, return_tensors="pt").to(device)
        out.append(model(enc["input_ids"], enc["attention_mask"]).float().cpu().numpy())
    return np.concatenate(out) if out else np.zeros((0, len(QUANTILES)))


def surprise(q, t):
    """P5: distance of t outside [q05, q95] in IQR units (0 inside)."""
    iqr = q[:, 3] - q[:, 1] + 0.01
    return np.maximum(np.maximum(q[:, 0] - t, t - q[:, 4]), 0.0) / iqr


def signed_log(y):
    return np.sign(y) * np.log10(1 + np.abs(y))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--members", nargs="+", type=Path, required=True)
    ap.add_argument("--eval", type=Path, required=True)
    ap.add_argument("--smoke-eval", action="store_true", help="apply every member to every table regardless of holdout (pipeline check only)")
    ap.add_argument("--max-len", type=int, default=1024)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    E = pd.DataFrame([json.loads(l) for l in a.eval.open() if l.strip()])
    texts = E.text.tolist(); t = E.t.to_numpy()
    preds = {}  # member -> (mask, q)
    for p in a.members:
        meta, tok, model = load_member(p, device)
        mask = np.ones(len(E), bool) if (a.smoke_eval or not meta["holdout_table"]) else (E.table == meta["holdout_table"]).to_numpy()
        q = predict(tok, model, [texts[i] for i in np.where(mask)[0]], device, min(a.max_len, meta["max_len"]))
        full = np.full((len(E), len(QUANTILES)), np.nan); full[mask] = q
        preds[p.name] = full
        print(f"member {p.name}: holdout={meta['holdout_table'] or 'none'} applied to {mask.sum()} events")
    Q = np.stack(list(preds.values()))  # members x events x 5
    S = np.stack([surprise(Q[m], t) for m in range(Q.shape[0])])  # members x events
    E["surprise"] = np.nanmedian(S, axis=0)
    E["epistemic"] = np.nanstd(Q[:, :, 2], axis=0)
    E["q05"], E["q50"], E["q95"] = np.nanmedian(Q[:, :, 0], 0), np.nanmedian(Q[:, :, 2], 0), np.nanmedian(Q[:, :, 4], 0)
    E["n_members"] = (~np.isnan(S)).sum(0)
    # sanity rows: clean value x1000 and /1000 (P5)
    clean = E[E.label == 0]
    for name, f in (("s_hi", 1000.0), ("s_lo", 1 / 1000.0)):
        ts = signed_log(clean.y.to_numpy() * f)
        Sx = np.stack([surprise(Q[m][clean.index.to_numpy()], ts) for m in range(Q.shape[0])])
        E.loc[clean.index, name] = np.nanmedian(Sx, axis=0)
    out = a.out or a.eval.with_name(a.eval.stem + "_scorer.jsonl")
    E.to_json(out, orient="records", lines=True)

    auc = lambda g, c: (lambda h: None if h.label.nunique() < 2 or h[c].nunique() < 2 else float(roc_auc_score(h.label, h[c])))(g.dropna(subset=[c]))
    def within(g, c):
        per = [auc(x, c) for _, x in g.groupby("table")]; per = [p for p in per if p is not None]
        if not per: return None, None
        rs = np.random.default_rng(1); bs = [np.mean(rs.choice(per, len(per), replace=True)) for _ in range(2000)]
        return float(np.mean(per)), [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
    f = lambda x: "  NA " if x is None else f"{x:.3f}"
    scored = E.dropna(subset=["surprise"])
    ps = scored[scored.severity.isin(["plausible", "subtle"])]
    cov = float(((clean.t >= E.loc[clean.index, "q05"]) & (clean.t <= E.loc[clean.index, "q95"])).mean())
    print(f"\n{a.eval.name}: {len(scored)} events scored (pos {int(scored.label.sum())}); clean coverage in [q05,q95] = {cov:.2f} (P5 window 0.80-0.98)")
    sh = pd.concat([clean.assign(label=0, s=E.loc[clean.index, "surprise"]), clean.assign(label=1, s=E.loc[clean.index, "s_hi"])])
    sl = pd.concat([clean.assign(label=0, s=E.loc[clean.index, "surprise"]), clean.assign(label=1, s=E.loc[clean.index, "s_lo"])])
    print(f"sanity: s_hi {f(auc(sh, 's'))}  s_lo {f(auc(sl, 's'))}  (hard rule > 0.95)")
    for c in ("surprise", "epistemic"):
        w, ci = within(scored, c); wp, cip = within(ps, c)
        print(f"{c:10s} pooled {f(auc(scored, c))}  within {f(w)} {['%.2f'%x for x in ci] if ci else ''}  | plausible+subtle within {f(wp)} {['%.2f'%x for x in cip] if cip else ''}")
    print("by severity (surprise):", {sv: f(auc(pd.concat([g, scored[scored.label == 0]]), "surprise")) for sv, g in scored[scored.label == 1].groupby("severity")})
    print("by template (surprise):", {tn: f(auc(g, "surprise")) for tn, g in scored.groupby("template")})
    print("wrote", out)


if __name__ == "__main__":
    main()
