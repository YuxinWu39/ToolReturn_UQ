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
import sys
from pathlib import Path

import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cached_metrics import scorer_summary

QUANTILES = [0.05, 0.25, 0.5, 0.75, 0.95]

HERE = Path(__file__).resolve().parent


def load_member(path, device):
    import torch
    from train_scorer import QuantileScorer, load_backbone
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


def predict(tok, model, texts, device, max_len, batch=16):
    import torch
    out = []
    for b in range(0, len(texts), batch):
        enc = tok(texts[b:b + batch], padding=True, truncation=True, max_length=max_len, return_tensors="pt").to(device)
        with torch.no_grad():
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
    ap.add_argument("--members", nargs="+", type=Path)
    ap.add_argument("--cached", type=Path, help="summarize saved predictions without loading torch or model weights")
    ap.add_argument("--eval", type=Path)
    ap.add_argument("--smoke-eval", action="store_true", help="apply every member to every table regardless of holdout (pipeline check only)")
    ap.add_argument("--max-len", type=int, default=1024)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    if a.cached:
        if a.members or a.eval:
            ap.error("--cached cannot be combined with --members/--eval")
        E = pd.read_json(a.cached, lines=True)
        report = scorer_summary(E)
        text = json.dumps(report, indent=2, allow_nan=False)
        if a.out:
            a.out.write_text(text + "\n")
        else:
            print(text)
        return
    if not a.members or not a.eval:
        ap.error("inference requires --members and --eval; use --cached for saved predictions")
    import torch
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

    report = scorer_summary(E)
    summary_path = out.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print("clean coverage:", report["clean_coverage"], "gate:", report["gate_pass"])
    print("real-corruption efficacy:", report["real_corruption_status"])
    print("wrote", out, summary_path)


if __name__ == "__main__":
    main()
