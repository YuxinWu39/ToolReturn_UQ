import io
import unittest

import numpy as np
import pandas as pd

import context_evidence_resample as cr


class ResamplingTest(unittest.TestCase):
    def test_provider_is_deterministic_eligible_and_visible_only(self):
        df=pd.DataFrame({'g':['a']*35+['b']*5,'x':list(range(40))})
        df.loc[0,'x']=np.nan
        q={'task_id':'q','filter':['g','a'],'column':'x','truth':123456.789,'corrupted':987654.321}
        a=cr.sample_evidence(df,q,0)
        self.assertEqual(a,cr.sample_evidence(df,q,0))
        self.assertNotEqual(a['row_indices'],cr.sample_evidence(df,q,1)['row_indices'])
        self.assertEqual(len(set(a['row_indices'])),20)
        shown=pd.read_csv(io.StringIO(a['evidence']['rows_csv']))
        self.assertEqual(len(shown),20)
        self.assertTrue((shown['g']=='a').all())
        self.assertTrue(np.isfinite(shown['x']).all())
        self.assertNotIn('truth',a['evidence'])
        self.assertNotIn('corrupted',a['evidence'])
        self.assertNotIn(str(q['truth']),a['evidence']['rows_csv'])

    def test_draw_units_do_not_become_table_clusters(self):
        rows=[{'dataset':d,'role':'clean','decision':'flag' if d=='A' else 'compatible'}
              for d in ('A','B') for _ in range(40)]
        rows += [{'dataset':d,'role':'corrupted','decision':'flag'} for d in ('A','B') for _ in range(40)]
        s=cr.flag_rates(rows)
        self.assertEqual(s['clean']['tables'],2)
        self.assertEqual(s['clean']['draw_units'],80)
        self.assertEqual(s['clean']['mean'],.5)
        self.assertEqual(s['clean']['flags'],40)


if __name__=='__main__':unittest.main()
