import numpy as np
from typing import Union
import pandas as pd
import pathlib


def concentration(asset_list: pd.DataFrame) -> pd.DataFrame:
    """

    :param asset_list:
    :return:
    """
    # Total amount of assets considered in this module:
    assets_xl = asset_list.exposure.sum()

    conc_factors = pd.read_csv(pathlib.Path(__file__).parent.joinpath('conc_factors.csv'), index_col=[0, 1])
    df = asset_list.merge(conc_factors, on=["exposure_type", "cc_step"], how="left")

    # Credit quality step 7 is unrated
    credit_threshold = {0: 0.03, 1: 0.03, 2: 0.03, 3: 0.015, 4: 0.015, 5: 0.015, 6: 0.015, 7: 0.015}
    # Relative excess exposure threshold
    df['ct'] = df.cc_step.map(credit_threshold)

    df.exposure = df.exposure.fillna(0.)
    df["xs_exposure"] = df.apply(lambda x: max(0., x.exposure / assets_xl - x.ct), axis=1)

    df['Conc'] = df.xs_exposure * df.gi * df.assets_xl
    mkt_conc = np.square(df.Conc).sum() ** 0.5

    return mkt_conc


def spread(bonds=None, securities=None, credit_derivatives=None) -> float:
    """
    Each item should be a pd.DataFrame with columns: mv, cc_step, duration
    """

    if bonds is not None:
        bonds['f_up'] = bonds.apply(lambda x: f_up(x.cc_step, x.duration, type=x.type), axis=1)
        bonds['delta_bof'] = bonds.mv * bonds.f_up
        mkt_spread_bonds = max(0., bonds.delta_bof.sum())
    else:
        mkt_spread_bonds = 0.
    if securities is not None:
        securities['f_up'] = securities.apply(lambda x: f_up(x.cc_step, x.duration, type=x.type), axis=1)
        securities['delta_bof'] = securities.mv * securities.f_up
        mkt_spread_sec = max(0., bonds.delta_bof.sum())
    else:
        mkt_spread_sec = 0.
    if credit_derivatives is not None:
        raise NotImplementedError
    else:
        mkt_spread_cd = 0.

    mkt_spread = mkt_spread_bonds + mkt_spread_sec + mkt_spread_cd
    return mkt_spread


def f_up(cc_step: int, duration: int, type: str = 'bonds') -> float:
    """
    Factor to apply to market value in stress
    :param cc_step: maps to rating 0-6, & 7 is unrated.
    :param duration:
    :param type: bonds, ri_no_mcr, eea_covered, gov_eea ,gov_non_eea, sec_type1, sec_type2, resec
    :return:

    f = alpha + beta * (duration - duration index adjustment)
    """
    if type == 'bonds':
        # Duration index 0-5
        dur_index = int(min(duration // 5, 4))
        duration_adjustment = dur_index * 5
        print(dur_index)
        # Row is duration, column is cc_step
        alpha = np.array([
            [0., 0., 0., 0., 0., 0., 0., 0.],
            [0.045, 0.055, 0.07, 0.125, 0.225, 0.375, 0.375, 0.15],
            [0.07, 0.084, 0.105, 0.2, 0.35, 0.585, 0.585, 0.235],
            [0.095, 0.109, 0.13, 0.25, 0.44, 0.61, 0.61, 0.235],
            [0.12, 0.134, 0.155, 0.3, 0.465, 0.635, 0.635, 0.355]])
        beta = np.array([
            [0.009, 0.011, 0.014, 0.025, 0.045, 0.075, 0.075, 0.03],
            [0.005, 0.006, 0.007, 0.015, 0.025, 0.042, 0.042, 0.017],
            [0.005, 0.005, 0.005, 0.01, 0.018, 0.005, 0.005, 0.012],
            [0.005, 0.005, 0.005, 0.01, 0.005, 0.005, 0.005, 0.0116],
            [0.005, 0.005, 0.005, 0.005, 0.005, 0.005, 0.005, 0.005]])
        print(alpha[dur_index][cc_step])
        f = alpha[dur_index][cc_step] + beta[dur_index][cc_step] * (duration - duration_adjustment)
    elif type == 'ri_no_mcr':
        dur_index = int(min(duration // 5, 4))
        duration_adjustment = dur_index * 5
        alpha = np.array([0., 0.375, 0.585, 0.61, 0.635])
        beta = np.array([0.075, 0.042, 0.005, 0.005, 0.005])
        f = alpha[dur_index] + beta[dur_index] * (duration - duration_adjustment)
    elif type == 'ri_no_mcr':
        dur_index = int(min(duration // 5, 1))
        duration_adjustment = dur_index * 5
        # Row is duration, column is cc_step
        alpha = np.array([
            [0., 0.],
            [0.035, 0.045]])
        beta = np.array([
            [0.007, 0.009],
            [0.005, 0.005]])
        f = alpha[dur_index][cc_step] + beta[dur_index][cc_step] * (duration - duration_adjustment)
    elif type == 'gov_eea':
        f = 0.
    elif type == 'gov_non_eea':
        dur_index = int(min(duration // 5, 1))
        duration_adjustment = dur_index * 5
        alpha = np.array([
            [0., 0., 0., 0., 0., 0., 0., 0.],
            [0., 0., 0.055, 0.07, 0.125, 0.225, 0.225, 0.225],
            [0., 0., 0.084, 0.105, 0.2, 0.35, 0.35, 0.35],
            [0., 0., 0.109, 0.13, 0.25, 0.44, 0.44, 0.44],
            [0., 0., 0.134, 0.155, 0.3, 0.465, 0.465, 0.465]])
        beta = np.array([
            [0., 0., 0.011, 0.014, 0.025, 0.045, 0.045, 0.045],
            [0., 0., 0.006, 0.007, 0.015, 0.025, 0.025, 0.025],
            [0., 0., 0.005, 0.005, 0.01, 0.018, 0.018, 0.018],
            [0., 0., 0.005, 0.005, 0.01, 0.005, 0.005, 0.005],
            [0., 0., 0.005, 0.005, 0.005, 0.005, 0.005, 0.005]])
        f = alpha[dur_index][cc_step] + beta[dur_index][cc_step] * (duration - duration_adjustment)
    elif type == 'sec_type1':
        beta = np.array([0.021, 0.042, 0.074, 0.085])
        f = beta[cc_step] * duration
    elif type == 'sec_type2':
        beta = np.array([0.125, 0.134, 0.166, 0.197, 0.82, 1., 1.])
        f = beta[cc_step] * duration
    elif type == 'resec':
        beta = np.array([0.33, 0.4, 0.51, 0.91, 1., 1., 1.])
        f = beta[cc_step] * duration
    return min(1., f)
