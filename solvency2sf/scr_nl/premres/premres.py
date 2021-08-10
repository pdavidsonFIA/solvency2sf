"""
This module calculates the premium and reserve risk

Directive 2015/35
Article 115-117

Test data:
import pandas as pd
dict_data = {
'vol_p': {
  ('EE', 'ass'): 1000,
  ('EE', 'liab'): 2000,
  ('EE', 'med'): 4000,
  ('EE', 'mod'): 3000,
  ('EE', 'mtpl'): 6000,
  ('EE', 'prop'): 20000,
  ('SE', 'ass'): 1000,
  ('SE', 'liab'): 2000,
  ('SE', 'med'): 4000,
  ('SE', 'mod'): 3000,
  ('SE', 'mtpl'): 6000,
  ('SE', 'prop'): 20000,
  ('WE', 'ass'): 1000,
  ('WE', 'liab'): 2000,
  ('WE', 'med'): 4000,
  ('WE', 'mod'): 3000,
  ('WE', 'mtpl'): 6000,
  ('WE', 'prop'): 20000},
   'vol_r': {
   ('EE', 'ass'): 2000,
  ('EE', 'liab'): 1000,
  ('EE', 'med'): 3000,
  ('EE', 'mod'): 5000,
  ('EE', 'mtpl'): 10000,
  ('EE', 'prop'): 7000,
     ('SE', 'ass'): 2000,
  ('SE', 'liab'): 1000,
  ('SE', 'med'): 3000,
  ('SE', 'mod'): 5000,
  ('SE', 'mtpl'): 10000,
  ('SE', 'prop'): 7000,
     ('WE', 'ass'): 2000,
  ('WE', 'liab'): 1000,
  ('WE', 'med'): 3000,
  ('WE', 'mod'): 5000,
  ('WE', 'mtpl'): 10000,
  ('WE', 'prop'): 7000,
  ('SE', 'ass'): 0.0,
  ('SE', 'liab'): 0.0,
  ('SE', 'med'): 0.0,
  ('SE', 'mod'): 0.0,
  ('SE', 'mtpl'): 0.0}}
volume_measures = pd.DataFrame(dict_data)
volume_measures.index.names=['s2region', 's2model']

"""

# Standard packages:
import os
import pathlib
import pandas as pd
import numpy as np


def get_factors(ins_sector='NL', ri_basis='net'):
    """
    Reads the standard deviation parameters for PR risk
     - gross or net,
     - H or NL
     Returns pandas dataframe indexed by s2model
    """
    fldr = pathlib.Path(__file__).parent.resolve()

    factors = pd.read_csv(os.path.join(fldr, 'factors.csv'))
    factors = factors.loc[factors.ins_sector == ins_sector]
    if ri_basis == 'net':
        factors['sd_pr'] = factors.sd_net_pr
    else:
        factors['sd_pr'] = factors.sd_gross_pr
    factors = factors[['s2model', 'sd_pr', 'sd_resv']].set_index('s2model')
    return factors


def get_corr(ins_sector='NL'):
    """
    Reads the correlation matrix for PR risk
     - H or NL
     Returns pandas dataframe indexed by s2model
    """
    fldr = pathlib.Path(__file__).parent.resolve()
    corr = pd.read_csv(os.path.join(fldr, 'corr_' + ins_sector.lower() + '.csv'), index_col=0)
    return corr


def scr_nl_premres(
        volume_measures: pd.DataFrame,
        ins_sector='NL',
        ri_basis='net'
):
    """
    SCR NL Premium and reserve risk
    volume measures:
    - p_vol
    - r_vol
    index:
    - s2 region: WE, EE, SE etc...
    - s2 lob aligned with the s2model definition for premium and reserve risk
    """
    vm = volume_measures.copy()
    vm['tot'] = vm.sum(axis=1)
    vm['tot2'] = vm.tot**2
    
    # Regional diversification:
    pr = vm.groupby('s2model').sum()
    pr['div_regions'] = pr.apply(lambda x: x.tot2/x.tot**2, axis=1)
    pr = pr.drop(columns=['tot2'])
    pr['voldiv'] = pr['tot'] * (0.75 + 0.25 * pr['div_regions'])

    # Bring in the premium & reserve standard deviation parameters:
    factors = get_factors(ins_sector, ri_basis)
    
    # Create a full index here for consistency with correlation matrix:
    pr = pr.merge(factors, how='right', on='s2model')

    # Weight the standard deviation:
    pr['sd'] = pr.apply(lambda x: 
                        (((x.vol_p*x.sd_pr)**2 + (x.vol_r*x.sd_resv)**2 +
                                    (x.vol_p*x.sd_pr*x.vol_r*x.sd_resv))**0.5)/x.tot, 
                        axis=1)
    pr = pr.fillna(0)
    vol = pr.voldiv.sum()
    corr = get_corr(ins_sector)

    # Apply correlation matrix across the lob's:
    sd = np.matmul((pr.sd*pr.voldiv).T, np.matmul(corr,(pr.sd*pr.voldiv)))**0.5 / vol

    scr = 3 * vol * sd

    # TODO: Add qrt output
    return scr
