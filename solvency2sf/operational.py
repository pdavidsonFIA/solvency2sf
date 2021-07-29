"""
SCR Op risk module
"""


def op_scr(
        gep_last12m: float,
        gep_prior12m: float,
        gross_tp: float,
        bscr
):
    """
    SCR Op Risk module

    Inputs:
    - Gross EP last 12m and 12m prior
    - Gross TP: BEL should be positive
    - BSCR
    """

    op_premiums = 0.03 * gep_last12m + 0.03 * max(0., gep_last12m - 1.2 * gep_prior12m)
    op_provisions = 0.03 * max(0., gross_tp)
    op = max(op_premiums, op_provisions)

    scr_op = min(op, 0.3*bscr)

    return scr_op, op
