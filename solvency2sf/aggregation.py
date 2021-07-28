"""
SCR Aggregation

This module takes the output from the different SCR sub-modules
and aggregates according to Solvency II Standard Formula correlation matrices.
"""

import math
import numpy as np
import pandas as pd


def scr_nl(
        scr_nl_pr_net,
        scr_nl_lapse,
        scr_nl_cat,
        corr_nl_uw
):
    """
    SCR NL
    This function aggregates the NL UW modules.
    Returns a series the same length as the individual SCR components
    """

    # Concatenate the inputs:
    scrs = [scr_nl_pr_net, scr_nl_cat, scr_nl_lapse]
    scrx = pd.concat(scrs, axis=1).fillna(0)

    # Make numpy array for the matrix multiplication:
    corr_arr = np.array(corr_nl_uw)
    # Reorder the columns to align with the correlation matrix:
    scrx = scrx[corr_nl_uw.columns]

    # Do the maths:
    scrx['v_arr'] = scrx.apply(lambda x: np.array(x[0:3]), axis=1)
    scrx['SCR_NL'] = scrx.apply(lambda x: math.sqrt(np.matmul(x.v_arr.T, np.matmul(corr_arr, x.v_arr))), axis=1)

    return scrx.SCR_NL


def bscr(
        scr_nl,
        scr_l,
        scr_h,
        scr_mkt,
        scr_def,
        corr_bscr
):
    """
    Basic SCR
    Aggregates the SCR another level and returns a series
    """
    scrs = [scr_nl, scr_mkt, scr_def, scr_l, scr_h]
    scrx = pd.concat(scrs, axis=1)

    # Create a shell dataframe and update with components that are present
    scry = pd.DataFrame(index=scrx.index, columns=corr_bscr.columns)
    scry.update(scrx)
    # Fill in the blanks with 0's:
    scry = scry.fillna(0)

    # Make numpy array for the matrix multiplication:
    corr_arr = np.array(corr_bscr)

    # Do the maths:
    scry['v_arr'] = scry.apply(lambda x: np.array(x[0:5]), axis=1)
    scry['BSCR'] = scry.apply(lambda x: math.sqrt(np.matmul(x.v_arr.T, np.matmul(corr_arr, x.v_arr))), axis=1)

    return scry.BSCR


def scr_op_rm(
        bscr,
        g_res_vol=None,
        scr_op_old=None
):
    """
    SCR Op used in risk margin module
    """
    # this function calculates the scr_op in two different cases
    # TODO: Complete the function and add exception, only 2 of the three arguments should be used

    if scr_op_old is not None:
        df = pd.concat([bscr, scr_op_old], axis=1)
        df.columns = ["bscr", "scr_op_old"]
        df["scr_op"] = min(float(df["bscr"] * 0.3), float(df["scr_op_old"]))
        name = "scr_op_t0"

    else:
        df = pd.concat([bscr, g_res_vol], axis=1)
        df.columns = ["bscr", "g_res_vol"]
        scr_op = []
        for i in df.index:
            scr_op.append(min(0.03 * df["g_res_vol"][i], df["bscr"][i] * 0.3))
        df["scr_op"] = scr_op
        name = "scr_op_t1n"

    return df.scr_op

    # run_type = val.runtype if workspace is None else None
    # filepath = val.workspace.output_scr + name + '.pkl' if workspace is None else workspace + name + '.pkl'
    #
    # r1 = ResultItem(name=name, source_model='aggregation', filepath=filepath, data=df["scr_op"], run_type=run_type)
    #
    # return tuple([r1])


def scr_total(
        bscr,
        scr_op
):
    """ This function simply adds the SCR_Op to the BSCR """
    scrx = pd.concat((bscr, scr_op), axis=1)
    scrx['SCR'] = scrx.sum(axis=1)
    return scrx.SCR
