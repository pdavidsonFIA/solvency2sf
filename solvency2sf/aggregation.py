"""
SCR Aggregation

This module takes the output from the different SCR sub-modules
and aggregates according to Solvency II Standard Formula correlation matrices.
"""
import os
import pathlib
import numpy as np


def load_corrmat(module_name: str):
    fldr = pathlib.Path(__file__).parent.resolve()
    corr = np.genfromtxt(os.path.join(fldr, 'corr_' + module_name + '.csv'), skip_header=1, delimiter=',')
    # Delete the index col:
    corr = np.delete(corr, 0, axis=1)
    return corr


def scr_agg(scr_submodules: np.array, module_name: str):
    """
    Aggregation of submodules according to selected corr mat
    scr_submodules:
    - array ordered consistently with the corr matrix
    - unused modules should be filled with 0.
    module_name: bscr, h_uw, nl_uw
    """
    corr = load_corrmat(module_name)
    scr = (np.matmul(scr_submodules.T, np.matmul(corr, scr_submodules)))**0.5
    return scr


def scr_total(
        bscr,
        scr_op
):
    """ This function simply adds the SCR_Op to the BSCR """
    return bscr + scr_op
