"""
MCR Calculation
- Linear NL
- Linear L
- Combined
- Early warning indicator

import pandas as pd
tp_nl_net = pd.Series(
{'mtpl': 20000,
 'mod': 10000,
 'mar': 0,
 'prop': 21000,
 'liab': 2000,
 'cred': 0,
 'lexp': 0,
 'ass': 4000,
 'misc': 0,
 'np_cas_re': 0,
 'np_mar_re': 0,
 'np_prop_re': 0,
 'med': 6000,
 'ip': 0,
 'work': 0,
 'np_heal_re': 0}, name='tp_nl_net')
nwp = pd.Series(
{'mtpl': 500,
 'mod': 500,
 'mar': 500,
 'prop': 500,
 'liab': 500,
 'cred': 500,
 'lexp': 500,
 'ass': 500,
 'misc': 500,
 'np_cas_re': 500,
 'np_mar_re': 500,
 'np_prop_re': 500,
 'med': 500,
 'ip': 500,
 'work': 500,
 'np_heal_re': 500}, name='nwp')
tp_l = pd.Series(
{1: 400,
 2: 0,
 3: 400,
 4: 800}, name='tp_l')
car_l = 10000
scr = 22785.9
"""

import os
import pathlib
import pandas as pd
import numpy as np


def get_factors():
    """
    Reads the factors used in the MCR calculation
     # - H or NL
     Returns pandas dataframe indexed by s2model
    """
    fldr = pathlib.Path(__file__).parent.resolve()
    factors = pd.read_csv(os.path.join(fldr, 'factors_mcr.csv'))

    factors = factors[['s2model', 'premium_beta', 'tp_alpha']].set_index('s2model')
    return factors


def mcr(
        nwp: pd.Series,
        tp_nl_net: pd.Series,
        tp_l: pd.Series,
        car_l: float,
        scr: float,
        debug_output={}
):
    """
    This function calculate:
     - MCR
     - MCR NL Linear
     - MCR L Linear
     """

    # Basic MCR parameters:
    amcr = 3700000
    ewi_l = 3
    ewi_nl = 1.75
    bound_floor = 0.25
    bound_cap = 0.45

    # MCR NL: TP should be input as positive liabilities. Floor to 0
    tp_nl_net = tp_nl_net.apply(lambda x: np.maximum(x, 0))
    df = pd.concat((tp_nl_net, nwp), axis=1)
    factors = get_factors()
    df = df.merge(factors, how='left', left_index=True, right_index=True)

    mcr_tp_nl = (df.tp_net * df.tp_alpha).sum()
    mcr_prem_nl = (df.nwp * df.premium_beta).sum()
    mcr_linear_nl = mcr_tp_nl + mcr_prem_nl

    # MCR Life: TP life grouped accoring to MCR definitions:
    tp_life_factors = pd.Series({1: 0.037, 2: -0.052, 3: 0.007, 4: 0.021}, name='factor_l')
    df_life = pd.concat((tp_l, tp_life_factors), axis=1)
    mcr_linear_l = df_life.product(axis=1).sum() + 0.0007 * car_l

    # MCR Combined:
    mcr_linear = mcr_linear_l + mcr_linear_nl
    mcr_cap = scr * bound_cap
    mcr_floor = scr * bound_floor
    mcr_combined = np.minimum(np.maximum(mcr_linear, mcr_floor), mcr_cap)
    mcr = np.maximum(mcr_combined, amcr)
    early_warning = ewi_l * mcr_linear_l + ewi_nl * mcr_linear_nl

    mcr_debug = {
            's28_01_01_02': df,
            's28_01_01_05': pd.DataFrame.from_dict({
                'mcr_linear': mcr_linear,
                'scr': scr,
                'mcr_cap': mcr_cap,
                'mcr_floor': mcr_floor,
                'mcr_combined': mcr_combined,
                'amcr': amcr,
                'mcr': mcr
            }, orient='index', columns=['C0070'])
        }
    debug_output['mcr'] = mcr_debug
    return mcr, debug_output
