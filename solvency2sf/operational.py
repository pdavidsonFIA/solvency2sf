"""
SCR Op risk module
import pandas as pd
data = {
'life_all':{'gep_last12m':1000, 'gep_prior12m':500, 'gross_tp':1600},
'nl':{'gep_last12m':500, 'gep_prior12m':200, 'gross_tp':63000},
'life_ul':{'gep_last12m':300, 'gep_prior12m':200, 'gross_tp':400}
}
df = pd.DataFrame.from_dict(data, orient='index')
gep = df.iloc[:,[0,1]]
gross_tp = df.iloc[:,2]
ul_exp = 250.
bscr = 20890.5
op_scr(gep, gross_tp, ul_exp, bscr)
"""
import pandas as pd


def op_scr(
        gep: pd.DataFrame,
        gross_tp: pd.DataFrame,
        ul_exp: float,
        bscr: float
):
    """
    SCR Op Risk module

    Inputs:
    - Gross EP last 12m and 12m prior
    - Gross TP: BEL should be positive
    - BSCR
    """

    op_premiums = \
        0.04 * (gep.at['life_all', 'gep_last12m'] - gep.at['life_ul', 'gep_last12m'])
    +        0.04 * max(0., (gep.at['life_all', 'gep_last12m'] - gep.at['life_ul', 'gep_last12m']) -
                        1.2 * (gep.at['life_all', 'gep_prior12m'] - gep.at['life_ul', 'gep_prior12m']))
    + 0.03 * gep.at['nl', 'gep_last12m'] + 0.03 * max(0.,
                                                      gep.at['nl', 'gep_last12m'] - 1.2 * gep.at['nl', 'gep_prior12m'])
    op_provisions = 0.0045 * max(0.,
                                 gross_tp.at['life_all'] - gross_tp.at['life_ul']) + 0.03 * max(0., gross_tp.at['nl'])
    op = max(op_premiums, op_provisions)

    scr_op = min(op, 0.3*bscr) + 0.25*ul_exp

    return scr_op, op
