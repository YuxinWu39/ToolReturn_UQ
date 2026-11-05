#!/usr/bin/env python3
"""P5 step 2: train one C3 scorer ensemble member (quantile head on Qwen2.5-0.5B + LoRA, pinball loss).

    python train_scorer.py --holdout-table public_penguins_v3.csv --seed 0 --out ../../models/scorer/penguins_s0
    python train_scorer.py --smoke            # 64 examples, 1 epoch, tiny max-len, CPU/MPS, to check the pipeline

LOTO: every training example whose table == --holdout-table is dropped (P5). Each member trains on an 80%
bootstrap of the remaining set drawn with --seed (P5 ensemble). Saves: adapter (or full head), head.pt, meta.json.
"""
import argparse
import json
import math
import random
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn

QUANTILES = [0.05, 0.25, 0.5, 0.75, 0.95]
DATA = Path(__file__).resolve().parents[2] / "data" / "ours" / "scorer"


class QuantileScorer(nn.Module):
    def __init__(self, backbone, hidden):
        super().__init__()
        self.backbone = backbone
        self.head = nn.Sequential(nn.Linear(hidden, 256), nn.GELU(), nn.Linear(256, len(QUANTILES)))

    def forward(self, input_ids, attention_mask):
        out = self.backbone(input_ids=input_ids, attention_mask=attention_mask)
        h = out.last_hidden_state
        last = attention_mask.sum(1) - 1  # last non-pad token (right padding)
        pooled = h[torch.arange(h.size(0), device=h.device), last]
        q = self.head(pooled.float())
        # monotone quantiles: q05 + cumulative softplus increments
        base = q[:, :1]
        inc = torch.nn.functional.softplus(q[:, 1:])
        return torch.cat([base, base + torch.cumsum(inc, dim=1)], dim=1)


def pinball(pred, target):
    t = target[:, None]
    qs = torch.tensor(QUANTILES, device=pred.device)[None, :]
    diff = t - pred
    return torch.mean(torch.maximum(qs * diff, (qs - 1) * diff))


def load_backbone(model_id, lora, device):
    from transformers import AutoModel, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(model_id)
    tok.padding_side = "right"
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    dtype = torch.bfloat16 if device == "cuda" else torch.float32
    bb = AutoModel.from_pretrained(model_id, dtype=dtype, attn_implementation="sdpa")  # eager attention OOMs at 16x1024 on 24 GB
    used_lora = False
    if lora:
        try:
            from peft import LoraConfig, get_peft_model
            cfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
            bb = get_peft_model(bb, cfg)
            used_lora = True
        except Exception as exc:  # noqa: BLE001
            print("peft unavailable, full fine-tune fallback (disclosed):", exc)
    if device == "cuda":
        bb.gradient_checkpointing_enable()
        if used_lora:
            bb.enable_input_require_grads()
    return tok, bb, used_lora


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", type=Path, default=DATA / "train.jsonl")
    ap.add_argument("--holdout-table", default="")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--model", default="Qwen/Qwen2.5-0.5B")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--grad-accum", type=int, default=1, help="micro-batches per optimizer step (effective batch = batch x grad-accum)")
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--max-len", type=int, default=1024)
    ap.add_argument("--bootstrap", type=float, default=0.8)
    ap.add_argument("--no-lora", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[2] / "models" / "scorer" / "smoke")
    a = ap.parse_args()
    random.seed(a.seed); np.random.seed(a.seed); torch.manual_seed(a.seed)
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")

    rows = [json.loads(l) for l in a.train.open() if l.strip()]
    rows = [r for r in rows if r["table"] != a.holdout_table]
    if a.smoke:
        rows, a.epochs, a.max_len, a.batch = rows[:64], 1, 256, 8
    rng = np.random.default_rng(a.seed)
    idx = rng.choice(len(rows), int(a.bootstrap * len(rows)), replace=True)  # P5: 80% bootstrap per member
    rows = [rows[i] for i in idx]
    print(f"device={device} train rows={len(rows)} holdout={a.holdout_table or 'none'} seed={a.seed} lora={not a.no_lora}")

    tok, bb, used_lora = load_backbone(a.model, not a.no_lora, device)
    model = QuantileScorer(bb, bb.config.hidden_size).to(device)
    params = [p for p in model.parameters() if p.requires_grad]
    print("trainable params:", sum(p.numel() for p in params))
    opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=0.01)
    steps = a.epochs * math.ceil(len(rows) / a.batch)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / max(1, int(0.06 * steps))) * max(0.0, (steps - s) / steps))

    t0 = time.time(); step = 0
    for ep in range(a.epochs):
        order = rng.permutation(len(rows)); tot = 0.0
        micro = max(1, a.batch // a.grad_accum)
        for b in range(0, len(rows), a.batch):
            batch = [rows[i] for i in order[b:b + a.batch]]
            opt.zero_grad(); bl = 0.0
            for mb in range(0, len(batch), micro):
                sub = batch[mb:mb + micro]
                enc = tok([r["text"] for r in sub], padding=True, truncation=True, max_length=a.max_len, return_tensors="pt").to(device)
                target = torch.tensor([r["t"] for r in sub], dtype=torch.float32, device=device)
                pred = model(enc["input_ids"], enc["attention_mask"])
                loss = pinball(pred, target) * len(sub) / len(batch)
                loss.backward(); bl += loss.item()
            torch.nn.utils.clip_grad_norm_(params, 1.0); opt.step(); sched.step()
            loss = torch.tensor(bl)
            tot += bl * len(batch); step += 1
            if step % 20 == 0:
                print(f"ep {ep} step {step}/{steps} loss {loss.item():.4f} {time.time()-t0:.0f}s", flush=True)
        print(f"epoch {ep} mean pinball {tot/len(rows):.4f}", flush=True)

    a.out.mkdir(parents=True, exist_ok=True)
    if used_lora:
        model.backbone.save_pretrained(a.out / "adapter")
    else:
        torch.save(model.backbone.state_dict(), a.out / "backbone.pt")
    torch.save(model.head.state_dict(), a.out / "head.pt")
    (a.out / "meta.json").write_text(json.dumps({"model": a.model, "holdout_table": a.holdout_table, "seed": a.seed, "epochs": a.epochs, "lr": a.lr,
                                                 "max_len": a.max_len, "batch": a.batch, "bootstrap": a.bootstrap, "n_train": len(rows), "lora": used_lora,
                                                 "quantiles": QUANTILES, "seconds": round(time.time() - t0), "device": device, "smoke": a.smoke}, indent=1))
    print("saved", a.out)


if __name__ == "__main__":
    main()
