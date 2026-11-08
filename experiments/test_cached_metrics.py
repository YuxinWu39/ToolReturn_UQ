import unittest
import numpy as np
import pandas as pd
from cached_metrics import metrics, paired, join_baselines, scorer_summary, common_gain


def fixture():
    return pd.DataFrame([dict(task_id=f"{table}{i}", label=label, dataset=table, template="unfiltered",
                              severity="subtle", y=1 + label, score=0.0)
                         for table in ("a", "b") for i in range(2) for label in (0, 1)])


class CachedMetricTests(unittest.TestCase):
    def test_constant_tables_are_chance_not_missing(self):
        r = metrics(fixture(), "score")
        self.assertEqual((r["within_auroc"], r["constant_tables"], r["tables"]), (0.5, 2, 2))
        self.assertEqual(r["within_average_precision"], 0.5)

    def test_nonfinite_or_missing_counterpart_removes_entire_task(self):
        rows = fixture()
        rows.loc[0, "score"] = np.inf
        rows = rows.drop(index=2)
        h = paired(rows, ["score"])
        self.assertEqual(set(h.task_id), {"b0", "b1"})
        self.assertTrue(h.groupby("task_id").label.nunique().eq(2).all())

    def test_duplicate_and_metadata_conflict_rejected(self):
        rows = fixture()
        with self.assertRaises(ValueError):
            paired(pd.concat([rows, rows.iloc[:1]]), ["score"])
        rows.loc[0, "severity"] = "obvious"
        with self.assertRaises(ValueError):
            paired(rows, ["score"])

    def test_baseline_return_mismatch_rejected(self):
        rows = fixture().assign(surprise=0)
        baseline = rows.assign(**{"0d": 0.0, "0r_log": 0.0})
        baseline.loc[0, "y"] = 100
        with self.assertRaises(ValueError):
            join_baselines(rows, baseline)

    def test_gate_withholds_gain_and_keeps_support(self):
        rows = fixture().assign(surprise=0.0, epistemic=0.0, t=1.0, q05=0.0, q95=2.0, s_hi=0.0, s_lo=0.0)
        report = scorer_summary(rows.rename(columns={"dataset": "table"}))
        self.assertFalse(report["gate_pass"])
        self.assertEqual(report["sanity"]["s_hi"]["within_auroc"], 0.5)
        gain = common_gain(rows.assign(**{"0d": 0.0, "0r_log": 0.0}), False)
        self.assertIsNone(gain["gain"])
        self.assertEqual(gain["common_tasks"], 4)

    def test_gain_uses_maximum_of_mean_baselines(self):
        rows = fixture()
        rows["surprise"] = rows.label
        rows["0d"] = np.where(rows.dataset == "a", rows.label, 1 - rows.label)
        rows["0r_log"] = 1 - rows["0d"]
        r = common_gain(rows, True)
        self.assertEqual(r["gain"], 0.5)  # max(mean AUCs)=.5, not mean(per-table max)=1
        self.assertEqual(r["ci95"], [0.0, 0.5])


if __name__ == "__main__":
    unittest.main()
