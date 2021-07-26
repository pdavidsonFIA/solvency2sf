"""
Dummy data for tests / debug
"""
import pandas as pd

class Dummy_Data:
    def __init__(self):
        self.liab_vol = pd.DataFrame(list(zip([200, 400000, 0, 50000, 0]*3, [0, 10000, 0, 10000, 0]*3)),
                                     index=pd.MultiIndex.from_product((range(1, 6), ['DE', 'CH', 'PL'])),
                                columns=['gep', 'limit_indem']).sort_index()
        self.liab_vol.index.names = ['grp_liab', 'country_isocode']
