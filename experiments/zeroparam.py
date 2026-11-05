"""Shared zero-parameter signals (A-P3b). One implementation for every script.

  range_score(y, lo, hi)                         normalized distance outside [lo, hi]; 0 inside
  rule_0a / rule_0b(op, y, vis_values, n)        range check / z-score from visible values
  bootstrap_0d(stat_fn, vis_df, k, n, B, rng)    percentile interval of a statistic over k-row resamples
  reference_0r(op, y, vis_values, n)             analytic signed t-score (|t| is the detection score)
  template_stat(op, column, flt, group)          pandas closure for a P3 template query
  is_sum_type(code)                              A-P3d AST rule: sum-type statistic -> scale by n/k
  oracle_law / score_0o_star                     A-P3d draw-conditioned oracle 0o*
"""

import math

import numpy as np
import pandas as pd

EPS = 1e-9
MEDIAN_SE_FACTOR = 1.2533  # sqrt(pi/2)


def range_score(y, lo, hi, floor=0.01):
    """Distance outside [lo, hi], normalized by the interval width with a floor of `floor` x the interval's
    magnitude so near-degenerate intervals (k identical values, exact counts) do not produce unbounded scores."""
    width = (hi - lo) + floor * (abs(lo) + abs(hi)) / 2 + EPS
    return max(lo - y, y - hi, 0.0) / width


def _stats(values):
    v = np.asarray(values, dtype=float)
    v = v[~np.isnan(v)]
    if len(v) == 0:
        return None
    return float(v.min()), float(v.max()), float(v.mean()), float(v.std(ddof=0)) if len(v) > 1 else 0.0, len(v)


def rule_0a(op, y, vis_values, n):
    """Location ops -> [min,max] of visible values; sum -> n*[min,max]; count -> [0,n]."""
    if op == "count":
        return range_score(y, 0.0, float(n))
    st = _stats(vis_values)
    if st is None:
        return None
    lo, hi = st[0], st[1]
    if op == "sum":  # A-P3d: a filtered/grouped sum over m < n rows can be below n*min
        lo, hi = n * min(lo, 0.0), n * max(hi, 0.0)
    return range_score(y, lo, hi)


def rule_0b(op, y, vis_values, n):
    if op == "count":
        return None
    st = _stats(vis_values)
    if st is None or st[3] == 0:
        return None
    mu, sd = st[2], st[3]
    if op == "sum":
        mu, sd = n * mu, n * sd
    return abs(y - mu) / (sd + EPS)


def reference_0r(op, y, vis_values, n):
    """Signed t-score (A-P3b). Returns (signed_t, unsigned_score) or (None, None)."""
    if op == "count":  # filtered counts are not n: use the [0, n] range (same as 0a)
        sc = range_score(y, 0.0, float(n))
        return (math.copysign(sc, y - n) if sc else 0.0, sc)
    st = _stats(vis_values)
    if st is None or st[4] < 2 or st[3] == 0:
        return None, None
    _, vmax, m, s, k = st
    if op == "max":
        t = max(y - vmax, 0.0) / (max(s, 0.01 * abs(vmax)) + EPS)
        return t, t
    if op == "median":
        se = MEDIAN_SE_FACTOR * max(s, 0.01 * abs(m)) / math.sqrt(k)
        t = (y - m) / (se + EPS)
        return t, abs(t)
    m_hat = m * n if op == "sum" else m
    s_hat = s * n if op == "sum" else s
    s_hat = max(s_hat, 0.01 * abs(m_hat))  # sd floor: 1% of the location, so near-constant columns stay finite
    t = (y - m_hat) / (s_hat / math.sqrt(k) + EPS)  # linear t (A-P3b clarification: one branch for every y)
    return t, abs(t)


def bootstrap_0d(stat_fn, vis_df, n, B, rng, scale_sum=False):
    """Interval of stat_fn over B resamples of size k=len(vis_df) (A-P3b). Returns (lo, hi) or None.

    stat_fn(df) -> float or None. If scale_sum, outputs are multiplied by n/k (sum-type statistics).
    Not computable if > 20% of resamples fail.
    """
    k = len(vis_df)
    if k == 0:
        return None
    outs, failed = [], 0
    factor = n / k if scale_sum else 1.0
    for _ in range(B):
        sample = vis_df.sample(n=k, replace=True, random_state=int(rng.integers(0, 2**31 - 1))).reset_index(drop=True)
        try:
            val = stat_fn(sample)
        except Exception:
            val = None
        if val is None or (isinstance(val, float) and math.isnan(val)):
            failed += 1
        else:
            outs.append(float(val) * factor)
    if failed > 0.2 * B or not outs:
        return None
    return float(np.percentile(outs, 2.5)), float(np.percentile(outs, 97.5))


def interval_score(y, interval):
    return None if interval is None else range_score(y, interval[0], interval[1])


def template_stat(op, column, flt, group):
    """pandas closure with the same semantics as the template code in gen_tasks.template_code."""
    def fn(df):
        if group:
            per = df.groupby(group)[column].apply(lambda s: _agg(s, op))
            per = per.dropna()
            return None if per.empty else float(per.max())
        sub = df[df[flt[0]].astype(str) == flt[1]] if flt else df
        if op == "count":
            return float(len(sub))
        if len(sub) == 0:
            return None
        return _agg(sub[column], op)
    return fn


def _agg(series, op):
    s = pd.to_numeric(series, errors="coerce").dropna()
    if op == "count":
        return float(len(s))
    if len(s) == 0:
        return None
    return float(getattr(s, op)())


# ----------------------------------------------------------------------------- A-P3c additions
import ast as _ast

SUM_TYPE_CALLS = {"sum", "count", "len", "size", "value_counts"}
# A-P3d round-6: nunique / len(unique()) count distinct values, which do not scale as n/k; location-type.
NON_SCALING_CALLS = {"nunique", "unique", "drop_duplicates"}
WRAPPERS = {"round", "float", "int", "abs", "print", "str"}
GROUP_REDUCERS = {"max", "min", "idxmax", "idxmin", "mean", "median", "sum", "head", "sort_values", "nlargest", "nsmallest"}


def _call_name(node):
    f = node.func
    return f.attr if isinstance(f, _ast.Attribute) else getattr(f, "id", None)


def _expr_is_sum_type(expr, assigns, depth=0):
    if depth > 20 or expr is None:
        return False
    if isinstance(expr, _ast.Name):  # print(total) -> look up total's assignment
        return _expr_is_sum_type(assigns.get(expr.id), assigns, depth + 1)
    if isinstance(expr, _ast.Subscript):  # df.shape[0]
        v = expr.value
        if isinstance(v, _ast.Attribute) and v.attr == "shape":
            return True
        return False
    if isinstance(expr, _ast.Attribute):  # bare attribute like df.size
        return expr.attr in ("size",)
    if not isinstance(expr, _ast.Call):
        return False
    name = _call_name(expr)
    if name in SUM_TYPE_CALLS:
        # len(df['x'].unique()) / df['x'].nunique(): count-distinct, not n/k-scaling
        if name == "len" and expr.args and isinstance(expr.args[0], _ast.Call) and _call_name(expr.args[0]) in NON_SCALING_CALLS:
            return False
        # sum over an aggregate that is itself location-type (groupby('g')['x'].mean().sum()) is not n/k-scaling
        if name == "sum" and isinstance(expr.func, _ast.Attribute) and isinstance(expr.func.value, _ast.Call) \
                and _call_name(expr.func.value) in ("mean", "median", "max", "min", "std", "var", "first", "last"):
            return False
        return True
    if name in NON_SCALING_CALLS:
        return False
    if name in WRAPPERS and isinstance(expr.func, _ast.Name):  # round(x, 2), print(x)
        return _expr_is_sum_type(expr.args[0] if expr.args else None, assigns, depth + 1)
    if isinstance(expr.func, _ast.Attribute):
        inner = expr.func.value
        if name in WRAPPERS:  # x.round(2) method form: look at the receiver
            return _expr_is_sum_type(inner, assigns, depth + 1)
        if name in GROUP_REDUCERS and isinstance(inner, _ast.Call):  # groupby(...).sum().max(), value_counts().max()
            return _expr_is_sum_type(inner, assigns, depth + 1)
    return False


def is_sum_type(code):
    """A-P3d rule: the statistic the code returns is sum-type (scaled by n/k) iff its last expression
    resolves to {sum, count, len, size, value_counts, nunique} or shape[0], looking through wrappers,
    method-form wrappers, print(name) after assignment, and reducers over a groupby aggregate."""
    try:
        tree = _ast.parse(code)
    except SyntaxError:
        return False
    if not tree.body:
        return False
    assigns = {}
    for node in tree.body:
        if isinstance(node, _ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, _ast.Name):
                    assigns[tgt.id] = node.value
    node = tree.body[-1]
    expr = node.value if isinstance(node, (_ast.Expr, _ast.Assign)) else None
    return _expr_is_sum_type(expr, assigns)


def reference_0r_log(op, y, vis_values, k_rows_template, filtered_or_grouped):
    """Registered 0r: log-ratio t for UNFILTERED mean/median only (A-P3c). Returns |t| or None."""
    if filtered_or_grouped or op not in ("mean", "median"):
        return None
    st = _stats(vis_values)
    if st is None or st[4] < 2 or st[3] == 0 or st[2] <= 0 or y <= 0:
        return None
    _, _, m, s, k = st
    s = max(s, 0.01 * abs(m))
    se = (MEDIAN_SE_FACTOR if op == "median" else 1.0) * s / (m * math.sqrt(k))
    return abs(math.log(y) - math.log(m)) / (se + EPS)


class FastTemplate:
    """numpy implementation of a P3 template statistic for repeated subset evaluation (0o)."""

    def __init__(self, df, op, column, flt, group):
        self.op, self.n = op, len(df)
        self.vals = pd.to_numeric(df[column], errors="coerce").to_numpy(dtype=float) if column else None
        self.mask = (df[flt[0]].astype(str) == flt[1]).to_numpy() if flt else None
        # NaN group keys are dropped (pandas groupby default): code -1
        self.codes = None
        if group:
            raw = df[group]
            codes = pd.factorize(raw.astype(str))[0]
            codes = np.where(raw.isna().to_numpy(), -1, codes)
            self.codes = codes

    def _agg(self, v):
        v = v[~np.isnan(v)] if v is not None else v
        if self.op == "count":
            return None
        if v is None or len(v) == 0:
            return None
        return {"mean": np.mean, "median": np.median, "max": np.max, "sum": np.sum}[self.op](v)

    def on_subset(self, idx):
        """Statistic on row indices idx with the 0d rules (undefined -> None; sum/count scaled by n/k)."""
        k = len(idx)
        scale = self.n / k
        if self.codes is not None:  # grouped: top group's aggregate
            codes, vals = self.codes[idx], self.vals[idx]
            best = None
            for c in np.unique(codes):
                if c < 0:  # NaN key
                    continue
                sel = vals[codes == c]
                if self.op == "count":  # pandas Series.count: non-null values
                    a = float(np.sum(~np.isnan(sel))) * scale
                else:
                    a = self._agg(sel)
                    if a is not None and self.op == "sum":
                        a *= scale
                if a is not None and (best is None or a > best):
                    best = a
            return best
        if self.mask is not None:
            sel = idx[self.mask[idx]]
            if self.op == "count":  # len(sub): defined (0) when no row matches, as in template_stat
                return float(len(sel)) * scale
            if len(sel) == 0:
                return None
            a = self._agg(self.vals[sel])
        else:
            if self.op == "count":
                return float(k) * scale
            a = self._agg(self.vals[idx])
        if a is not None and self.op == "sum":
            a *= scale
        return a


def oracle_0o(fast, k, M, rng):
    """A-P3c: sampling distribution of the k-row statistic over M random subsets of the full table.
    Returns (median, iqr, is_log) or None if > 20% undefined. See oracle_law for the A-P3d draw-conditioned form."""
    outs, undefined = [], 0
    for _ in range(M):
        idx = rng.choice(fast.n, k, replace=False)
        v = fast.on_subset(idx)
        if v is None or (isinstance(v, float) and math.isnan(v)):
            undefined += 1
        else:
            outs.append(float(v))
    if undefined > 0.2 * M or len(outs) < 10:
        return None
    arr = np.asarray(outs)
    if (arr > 0).all():
        la = np.log(arr)
        return float(np.median(la)), float(np.percentile(la, 75) - np.percentile(la, 25)), True
    return float(np.median(arr)), float(np.percentile(arr, 75) - np.percentile(arr, 25)), False


def score_0o(y, dist):
    """(signed, unsigned) distance of y from the oracle sampling distribution in IQR units."""
    if dist is None:
        return None, None
    med, iqr, is_log = dist
    if is_log:
        if y <= 0:
            return None, None
        d = (math.log(y) - med) / (iqr + EPS)
    else:
        d = (y - med) / (iqr + EPS)
    return d, abs(d)



def oracle_law(fast, k, M, rng, theta):
    """A-P3d: law of r = log(theta_hat_k / theta) (or theta_hat_k - theta when not all positive) over M
    random k-subsets of the full table. Returns (b_k, w_k, is_log, dist_0o) or None (> 20% undefined).
    dist_0o is the A-P3c population oracle from the same subsets, so both references share the draws."""
    outs, undefined = [], 0
    for _ in range(M):
        idx = rng.choice(fast.n, k, replace=False)
        v = fast.on_subset(idx)
        if v is None or (isinstance(v, float) and math.isnan(v)):
            undefined += 1
        else:
            outs.append(float(v))
    if undefined > 0.2 * M or len(outs) < 10:
        return None
    arr = np.asarray(outs)
    if (arr > 0).all() and theta > 0:
        la = np.log(arr)
        r = la - math.log(theta)
        dist = (float(np.median(la)), float(np.percentile(la, 75) - np.percentile(la, 25)), True)
        return float(np.median(r)), float(np.percentile(r, 75) - np.percentile(r, 25)), True, dist
    r = arr - theta
    dist = (float(np.median(arr)), float(np.percentile(arr, 75) - np.percentile(arr, 25)), False)
    return float(np.median(r)), float(np.percentile(r, 75) - np.percentile(r, 25)), False, dist


def score_0o_star(y, theta_hat_draw, law):
    """A-P3d draw-conditioned oracle: how implausible the observed k-row statistic is if y were the truth,
    given the exact k-row sampling law (bias b_k, spread w_k). (signed, unsigned) or (None, None)."""
    if law is None or theta_hat_draw is None or (isinstance(theta_hat_draw, float) and math.isnan(theta_hat_draw)):
        return None, None
    b, w, is_log, _ = law
    if is_log:
        if y <= 0 or theta_hat_draw <= 0:
            return None, None
        d = (math.log(theta_hat_draw) - math.log(y) - b) / (w + EPS)
    else:
        d = (theta_hat_draw - y - b) / (w + EPS)
    return d, abs(d)
