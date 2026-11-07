"""Offline tests for treatment integrity, grading and irreversible response retention."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

import context_pilot as cp


class ContextPilotTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = cp.prepare(cp.ROOT)

    def test_deterministic_selection_and_actual_evidence(self):
        self.assertEqual(cp.digest(self.m), cp.digest(cp.prepare(cp.ROOT)))
        for q in self.m['selected_queries']:
            df = pd.read_csv(cp.ROOT / 'data/ours/datasets' / q['dataset'])
            for u in self.m['units']:
                if u['task_id'] != q['task_id']:
                    continue
                rows = df.iloc[u['row_indices']]
                if u['context'] == 'matched20':
                    self.assertTrue((rows[q['filter'][0]].astype(str) == q['filter'][1]).all())
                    self.assertTrue(np.isfinite(pd.to_numeric(rows[q['column']])).all())
                text = u['messages'][1]['content']
                self.assertIn(rows.to_csv(index=False), json.loads(text.split('PARTIAL TABLE EVIDENCE\n')[1].split('\nTOOL RESULT')[0])['rows_csv'])
                self.assertNotIn('corrupted', text)
                self.assertNotIn('truth', text)
        bad = copy.deepcopy(self.m)
        bad['units'][0]['tool_packet']['answer'] = 123
        with self.assertRaises(AssertionError):
            cp.validate_manifest(bad)

    def test_parser_and_grading(self):
        good = {'decision':'accept','confidence':100,'answer':12.5,'reason':'mean 92 of 20'}
        self.assertEqual(cp.parse_reply(json.dumps(good)), good)
        for field, value in [('confidence', True), ('confidence', 100.0), ('confidence', 101),
                             ('answer', '12.5'), ('answer', False), ('answer', float('nan')),
                             ('decision', 'maybe'), ('reason', 12)]:
            bad = good | {field:value}
            self.assertIsNone(cp.parse_reply(json.dumps(bad)), (field,value))
        for raw in ['', '[]', 'null', '```json\n'+json.dumps(good)+'\n```']:
            self.assertIsNone(cp.parse_reply(raw))
        self.assertIsNone(cp.parse_reply(json.dumps(good | {'extra':True})))
        self.assertFalse(cp.close(None, 1, .01))

    def test_synthetic_constant_response_and_resume(self):
        from p4_run import SeededClient
        raw = json.dumps({'decision':'accept','confidence':100,'answer':None,'reason':'42 100 200'})
        body = {'model':'gemini-3.8-flash', 'usage':{'prompt_tokens':2,'completion_tokens':3,'total_tokens':5},
                'choices':[{'message':{'content':raw},'finish_reason':'stop'}]}
        with tempfile.TemporaryDirectory() as d, patch.dict('os.environ', {'GEMINI_API_KEY':'dummy'}), \
             patch.object(SeededClient, '_post', return_value=body) as api, contextlib.redirect_stdout(io.StringIO()):
            out = Path(d)
            cp.run(self.m, out, 'gemini-3.8-flash', 'https://example.test', 4)
            self.assertEqual(api.call_count, 72)
            cp.run(self.m, out, 'gemini-3.8-flash', 'https://example.test', 4)
            self.assertEqual(api.call_count, 72)  # completed invalid/valid responses never rerun
            s = cp.summarize(self.m, out)
            self.assertTrue(s['feasibility_pass'])
            self.assertEqual(s['usage']['total_tokens'], 360)
            self.assertIsNone(s['confidence_auroc']['estimate'])
            for v in s['primary_acceptance_discrimination_contrasts'].values():
                self.assertEqual(v['mean'], 0)
                self.assertEqual(v['ci95'], [0,0])
            for c in cp.CONTEXTS:
                self.assertEqual(s['cells'][c]['1']['correct'], 0)
                self.assertEqual(s['cells'][c]['1']['adopted_wrong'], 0)
            config = json.loads((out/'config.json').read_text())
            cp.save(out/'config.json', config | {'model':'different'})
            with self.assertRaisesRegex(ValueError, 'Resume config'):
                cp.run(self.m, out, 'gemini-3.8-flash', 'https://example.test', 4)

    def test_failure_recorded_and_stops_authentication(self):
        from p4_run import SeededClient
        with tempfile.TemporaryDirectory() as d, patch.dict('os.environ', {'GEMINI_API_KEY':'dummy'}), \
             patch.object(SeededClient, '_post', side_effect=RuntimeError('LLM request failed with HTTP 401: dummy')) as api, \
             contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(RuntimeError, 'transport failures'):
                cp.run(self.m, Path(d), 'gemini-3.8-flash', 'https://example.test', 1)
            self.assertEqual(api.call_count, 1)
            log = (Path(d)/'transport_failures.jsonl').read_text()
            self.assertNotIn('dummy',log)
            self.assertIn('[redacted]',log)


if __name__ == '__main__':
    unittest.main()
