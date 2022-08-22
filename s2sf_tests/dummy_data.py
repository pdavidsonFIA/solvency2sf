"""
Dummy data for s2sf_tests / debug
"""
import pandas as pd

class Dummy_Data:
    def __init__(self):
        self.liab_vol = pd.DataFrame(list(zip([200, 400000, 0, 50000, 0] * 3, [0, 10000, 0, 10000, 0] * 3)),
                                     index=pd.MultiIndex.from_product((range(1, 6), ['DE', 'CH', 'PL'])),
                                     columns=['gep', 'limit_indem']).sort_index()
        self.liab_vol.index.names = ['grp_liab', 'country_isocode']
        self.type_1 = pd.DataFrame.from_dict({
                                                "Bank A": {"balance": 1000000, "rating": 6, "category": 3, "mitigation": 0},
                                                "Bank B": {"balance": 1000000, "rating": 4, "category": 3, "mitigation": 0},
                                                'Bank C': {"balance": 10000000, "rating": 1, "category": 3, "mitigation": 0},
                                                'Reinsurer A': {"balance": 5000000, "rating": 1, "category": 1, "mitigation": 8000000}
                                            }, orient='index')
        self.scr_def_t1_expected = 882053.1516282775
        self.type_2 = pd.DataFrame.from_dict({"due_age":["overdue_more3m","other"], "balance": [500000,1000000]}).set_index('due_age')
        self.scr_def_t2_expected = 600000.0
        self.scr_def_expected = 1389915.680450734