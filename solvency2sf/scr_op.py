"""
SCR Op risk module
MCR and workflow
"""
import os
import pandas as pd
import numpy as np


def op_scr(
        premiumcube: pd.DataFrame,
        claims_provision: pd.DataFrame,
        premium_provision: pd.DataFrame,
        bscr
):
    """
    SCR Op Risk module

    Inputs:
    - Gross EP last 12m and 12m prior
    - Gross TP
    - BSCR
    """
    premdf = premiumcube.reset_index()
    premdf['rep_date'] = premdf.acc_month
    premdf.drop(columns='acc_month', inplace=True)

    px = premdf.reset_index()[['rep_date', 'gep',]].groupby(by=['rep_date']).sum()
    px['gep_cum'] = px.gep.cumsum()
    px['earn_nl'] = px.gep.rolling(12).sum().fillna(px.gep_cum)
    px['p_earn_nl'] =px.earn_nl.shift(12, fill_value=0)
    px['op_premiums'] = px.apply(lambda x:  0.03 * x.earn_nl + 0.03 * max(0, x.earn_nl - 1.2 * x.p_earn_nl), axis=1)

    cp = claims_provision['cp_gross'].groupby(by=['rep_date']).sum()
    pp = premium_provision['pp_gross'].groupby(by=['rep_date']).sum()

    # Change sign as liability is positive for this calc
    res = - pd.concat((cp, pp), axis=1)
    res['tp_nl'] = res.sum(axis=1)
    res['op_provisions'] = res.tp_nl.apply(lambda x: 0.03 * max(0,x))
    op = pd.concat((px.op_premiums, res.op_provisions), axis=1)
    op.dropna(inplace=True)
    op['Op'] = op[['op_premiums', 'op_provisions']].max(axis=1)

    opx = pd.concat((op, bscr), axis=1)
    opx['SCR_Op'] = opx.apply(lambda x: min(x.Op, 0.3*x.BSCR), axis=1)

    return opx[['Op', 'SCR_Op']]
