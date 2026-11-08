import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd

import experiment_a as exp
from experiment_a_python import execute, validate


def fixtures():
    rows = pd.DataFrame({'group':['a']*20, 'value':[99.,101.]*10}).to_csv(index=False)
    q = {'task_id':'test', 'dataset':'synthetic.csv', 'query':'mean value for group a',
         'code':"df[df['group']=='a']['value'].mean()", 'truth':100., 'tolerance':.01}
    evidence = {'unit_id':'test_draw0', 'task_id':'test', 'draw':0,
                'evidence': {'shape':[200,2], 'columns':['group','value'], 'rows_csv':rows}}
    feat = {'task_id':'test_draw0', 'finite_targets':20, 'interval_0d':[99.5,100.5]}
    units = exp.make_units([q], [evidence], [feat])
    return units, {'units':units, 'expected':9}


def body(raw):
    return {'choices':[{'message':{'content':raw}, 'finish_reason':'stop'}], 'model':exp.MODEL,
            'usage': {'prompt_tokens':10, 'completion_tokens':10, 'total_tokens':20}}


FINAL = json.dumps({'decision':'accept', 'confidence':50, 'answer':100., 'reason':'synthetic test'})


class ExperimentTests(unittest.TestCase):
    def test_all_arms_share_evidence_and_cross_candidates(self):
        units,m = fixtures()
        exp.validate_manifest(m)
        raw = next(u for u in units if u['arm']=='raw' and u['level']=='scale150')
        checked = next(u for u in units if u['arm']=='check' and u['level']=='scale150')
        self.assertEqual(raw['rows_csv'],checked['rows_csv'])
        self.assertNotIn('SAMPLE-BASED CHECK',raw['messages'][1]['content'])
        self.assertIn('SAMPLE-BASED CHECK',checked['messages'][1]['content'])
        self.assertTrue(checked['check']['flag'])

    def test_completed_invalid_never_regenerated(self):
        units,m = fixtures(); u = next(u for u in units if u['arm']=='raw')
        with tempfile.TemporaryDirectory() as d:
            with patch.object(exp,'request',return_value=body('```bad```')) as request:
                r = exp.run_unit(u,m,Path(d),'fake')
                self.assertFalse(r['valid'])
                self.assertEqual(r['status'],'completed')
                again = exp.run_unit(u,m,Path(d),'fake')
                self.assertEqual(request.call_count,1)
                self.assertEqual(r,again)

    def test_code_tool_uses_only_visible_csv_and_final_is_preserved(self):
        units,m = fixtures(); u = next(u for u in units if u['arm']=='code')
        def fake_request(payload,key,call,checkpoint):
            r = body(json.dumps({'python':"df['value'].mean()"}) if len(payload['messages'])==2 else FINAL)
            call['provider_response']=r
            checkpoint()
            return r
        with tempfile.TemporaryDirectory() as d:
            with patch.object(exp,'request',side_effect=fake_request) as request, patch.object(exp,'execute',return_value={'output':'100.0','error':False,'isolation':'test'}) as tool:
                r = exp.run_unit(u,m,Path(d),'fake')
                self.assertTrue(r['valid'])
                self.assertEqual(request.call_count,2)
                self.assertEqual(tool.call_args.args[0],u['rows_csv'])
                self.assertNotIn('truth',str(tool.call_args))
                exp.run_unit(u,m,Path(d),'fake')
                self.assertEqual(request.call_count,2)

    def test_length_terminated_valid_json_is_not_accepted_or_executed(self):
        units,m=fixtures(); u=next(u for u in units if u['arm']=='code')
        for raw in [FINAL, json.dumps({'python':"print(100)"})]:
            response=body(raw);response['choices'][0]['finish_reason']='length'
            with tempfile.TemporaryDirectory() as d, patch.object(exp,'request',return_value=response), patch.object(exp,'execute') as tool:
                r=exp.run_unit(u,m,Path(d),'fake')
                self.assertFalse(r['valid'])
                self.assertEqual(r['terminal_reason'],'truncated-or-refused')
                tool.assert_not_called()

    def test_primary_contrast_averages_tables_and_preserves_clean(self):
        from report_experiment_a import effect
        rows=[]
        for table in range(6):
            for arm in ('raw','check'):
                for level,_ in exp.LEVELS:
                    rows.append({'evidence_unit':f'q{table}_d0','task_id':f'q{table}','dataset':f't{table}',
                                 'arm':arm,'level':level,'valid':True,
                                 'decision':'accept' if arm=='raw' or level=='clean' else 'reject'})
        r=effect(rows,'check','raw')
        self.assertEqual(r['tables'],6)
        self.assertEqual(r['discrimination']['mean'],1.)
        self.assertEqual(r['discrimination']['ci95'],[1.,1.])
        self.assertEqual(r['clean_acceptance']['mean'],0.)

    def test_python_import_and_introspection_rejected(self):
        for code in ['import os', 'df.__class__', "__import__('os')"]:
            with self.assertRaises(ValueError): validate(code)

    def test_real_sandbox_mean_and_source_file_denial(self):
        u,_ = fixtures()
        rows=u[0]['rows_csv']
        normal=execute(rows,"import numpy as np\nprint(float(df['value'].mean()))")
        self.assertFalse(normal['error'])
        self.assertEqual(normal['output'],'100.0')
        forbidden=execute(rows,"pd.read_csv('/Users/yuxinwu/Desktop/ToolReturn_UQ/data/ours/datasets/public_abalone.csv')")
        self.assertTrue(forbidden['error'])
        self.assertEqual(forbidden['isolation'],'seatbelt-subprocess')


if __name__=='__main__':
    unittest.main()
