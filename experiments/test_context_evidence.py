"""Synthetic-only preflight tests for A-CTX-EVIDENCE; no measured pilot results."""
import copy
import io
import json
import unittest
from unittest.mock import patch

import pandas as pd

import context_evidence as ce


def evidence(csv='group,x\na,10\na,10\na,10\na,10\n'):
    return {'rows_csv':csv,'columns':['group','x'],'shape':[1000,2]}


def event(role,score=0.,task='t',dataset='d'):
    return {'task_id':task,'dataset':dataset,'role':role,'score':score,'decision':ce.decision(score)}


class EvidenceTest(unittest.TestCase):
    def test_only_displayed_csv_is_read(self):
        original=pd.read_csv
        def guarded(source,*args,**kwargs):
            self.assertIsInstance(source,io.StringIO)
            return original(source,*args,**kwargs)
        with patch.object(ce.pd,'read_csv',side_effect=guarded):
            f=ce.features(evidence(),'x',['group','a'],'t','matched20',B=32)
        self.assertEqual(f['finite_targets'],4)
        self.assertEqual(f['sample_mean'],10.)
        self.assertEqual(f['interval_0d'],[10.,10.])

    def test_displayed_hash_mismatch_is_rejected(self):
        e=evidence()
        messages=[{'role':'system','content':'test'},
                  {'role':'user','content':'PARTIAL TABLE EVIDENCE\n'+json.dumps(e)+'\nTOOL RESULT\n{"value":10}'}]
        u={'messages':messages,'messages_hash':ce.digest(messages),'context_hash':ce.digest(e)}
        self.assertEqual(ce.displayed_evidence(u),e)
        bad=copy.deepcopy(u);bad['context_hash']='bad'
        with self.assertRaises(AssertionError):ce.displayed_evidence(bad)

    def test_known_constant_case_and_interval_reuse(self):
        with patch.object(ce,'bootstrap_0d',return_value=(10.,10.)) as bootstrap:
            f=ce.features(evidence(),'x',['group','a'],'t','matched20',B=32)
            q={'task_id':'t','dataset':'d','severity':'subtle','truth':10.,'corrupted':11.}
            events=ce.events_for_query(q,'matched20',f)
        self.assertEqual(bootstrap.call_count,1)
        self.assertEqual(len(events),8)
        for method in ce.METHODS:
            sub=[e for e in events if e['method']==method]
            self.assertEqual([e['decision'] for e in sub],['compatible','flag','flag','flag'])
            s=ce.summarize_cell(sub)
            self.assertTrue(s['sanity_pass'])
            self.assertEqual(s['detection']['within_table'],1.)

    def test_undefined_filter_and_missing_scores(self):
        f=ce.features(evidence(),'x',['group','missing'],'t','head5',B=32)
        self.assertEqual(f['finite_targets'],0)
        self.assertIsNone(f['interval_0d'])
        for method in ce.METHODS:
            self.assertIsNone(ce.score(method,100,f))
        e=[event(r,None) for r in ('clean','corrupted','sanity_hi','sanity_lo')]
        s=ce.summarize_cell(e)
        self.assertFalse(s['sanity_pass'])
        self.assertEqual(s['policy']['clean']['unscorable'],1)
        self.assertIsNone(s['detection']['within_table'])

    def test_constant_scores_and_strict_gate(self):
        e=[event(r,0.) for r in ('clean','corrupted','sanity_hi','sanity_lo')]
        s=ce.summarize_cell(e)
        self.assertEqual(s['sanity']['within_table'],.5)
        self.assertFalse(s['sanity_pass'])
        self.assertIsNone(s['detection']['within_table'])
        self.assertFalse(ce.passes_sanity(None))
        self.assertFalse(ce.passes_sanity(.95))
        self.assertTrue(ce.passes_sanity(.950001))
        self.assertEqual(ce.decision(1e-10),'compatible')
        self.assertEqual(ce.decision(1e-8),'flag')

    def test_severity_cannot_bypass_failed_context_gate(self):
        es=[event('clean',0.),event('corrupted',1.),event('sanity_hi',100.),event('sanity_lo',1.)]
        s=ce.summarize_cell(es,parent_gate=False)
        self.assertTrue(s['local_sanity_pass'])
        self.assertFalse(s['sanity_pass'])
        self.assertIsNone(s['detection']['within_table'])
        self.assertIsNone(s['per_table']['d']['detection'])

    def test_common_support_and_model_format_failure(self):
        es=[event('clean',0.),event('corrupted',1.)]
        rows=[{'task_id':'t','label':0,'decision':'invalid','valid':False},
              {'task_id':'t','label':1,'decision':'accept','valid':True}]
        s=ce.model_comparison(es,rows,True)
        self.assertEqual(s['mean'],2.)
        self.assertEqual(s['invalid_model_cells'],1)
        self.assertEqual(s['common_support_decisions']['clean']['model']['invalid'],1)
        self.assertEqual(s['common_support_decisions']['corrupted']['model']['accept'],1)
        self.assertEqual(s['common_support_decisions']['corrupted']['baseline']['flag'],1)
        self.assertIsNone(ce.model_comparison(es,rows,True,True)['mean'])
        self.assertIsNone(ce.model_comparison(es,rows,False)['mean'])
        es[1]['score']=None;es[1]['decision']='unscorable'
        self.assertEqual(ce.model_comparison(es,rows,True)['queries'],0)

    def test_context_contrast_withheld_when_gate_fails(self):
        self.assertIsNone(ce.context_comparison([], 'matched20','random20',
                                             {'matched20':True,'random20':False})['mean'])

    def test_roles_are_paired_before_auc(self):
        es=[event('clean',0.),event('corrupted',1.),event('clean',100.,task='unpaired')]
        s=ce.auc_summary(es,('clean','corrupted'))
        self.assertEqual(s['paired_queries'],1)
        self.assertEqual(s['within_table'],1.)


if __name__=='__main__':
    unittest.main()
