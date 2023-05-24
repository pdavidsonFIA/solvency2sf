"""

cc_step: rating
0 : "AAA"
1 : "AA"
2 : "A"
3 : "BBB"
4 : "BB"
5 : "B"
6 : "CCC or lower"
7 : "Unrated"

exposure_types:
1 : "EEA governments and central banks denominated and funded in the domestic currency, multilateral banks and international organisations"
2 : "Standard"
3 : "Mortgage covered bond or public sector covered bonds exposure"
4 : "Property exposure"
5 : "non-EEA governments and central banks denominated and funded in the domestic currency exposures"

"""

import numpy as np
import pandas as pd


def equity(equities: pd.DataFrame, symmetric_adjustment: float) -> pd.DataFrame:
    """
    Shock = alpha + beta * symmetric_adjustment

    :param equities:
    :param symmetric_adjustment:
    :return:
    """
    shock_params = {
        'strategic_long_term': (0.22, 0.),
        'type1': (0.39, 1.),
        'type2': (0.49, 1.),
        'infra_corp': (0.36, 0.92),
        'infra_other': (0.3, 0.77),
    }
    equities['shock_params'] = equities.exposure_type.map(shock_params)
    equities['shock'] = equities.shock_params.apply(lambda param: param[0] + param[1] * symmetric_adjustment)
    equities['loss'] = equities.mv * equities.shock
    equities['shock_group'] = equities.exposure_type.map({'type1': 'type1'}).fillna('other')
    eq = equities.groupby('shock_group').sum()['loss']
    eq['scr'] = (eq.type1 ** 2 +
                 2 * 0.75 * eq.type1 * eq.other +
                 eq.other ** 2) ** 0.5
    return eq


def concentration(asset_list: pd.DataFrame) -> float:
    """
    asset_list should be a pd.Dataframe with columns:
    - mv: market value
    - type:
    - cc_step: 0-6 & 7 is unrated

    asset_list = pd.DataFrame([[10.   , 1   , 2],
       [20.   , 3   , 3],
       [70.   , 2   , 7]], columns=['mv', 'exposure_type', 'cc_step'])

    :param asset_list:
    :return:
    """
    # Total amount of assets considered in this module:
    assets_xl = asset_list.mv.sum()

    asset_list['gi'] = asset_list.apply(lambda x: gi(x.cc_step, exposure_type=x.type), axis=1)

    # Credit quality step 7 is unrated
    credit_threshold = [0.03, 0.03, 0.03, 0.015, 0.015, 0.015, 0.015, 0.015]

    # Relative excess exposure threshold
    asset_list['ct'] = asset_list.cc_step.apply(credit_threshold.__getitem__)

    asset_list.mv = asset_list.mv.fillna(0.)
    asset_list["xs_exposure"] = asset_list.apply(lambda x: max(0., x.mv / assets_xl - x.ct), axis=1)

    asset_list['Conc'] = asset_list.xs_exposure * asset_list.gi * asset_list.assets_xl
    mkt_conc = np.square(asset_list.Conc).sum() ** 0.5

    return mkt_conc


def gi(cc_step: int, exposure_type: str) -> float:
    if type == 'ri_mcr':
        # cc step mapping should  translate to solvency ratios
        gi_table = [0.12, 0.21, 0.27, 0.645, 0.73]
        return gi_table[min(4, cc_step)]
    if type == 'unrated_credit_financial':
        return 0.645
    if type == 'single_property':
        return 0.12
    if type == 'gov_eea':
        return 0.
    if type == 'gov_non_eea':
        gi_table = [0., 0., 0.12, 0.21, 0.27, 0.73, 0.73, 0.73]
        return gi_table[cc_step]
    else:
        gi_table = [0.12, 0.12, 0.21, 0.27, 0.73, 0.73, 0.73, 0.73]
        return gi_table[cc_step]


def spread(bonds=None, securities=None, credit_derivatives=None) -> float:
    """
    Each item should be a pd.DataFrame with columns: mv, cc_step, duration
    """
    if bonds is not None:
        bonds['f_up'] = bonds.apply(lambda x: f_up(x.cc_step, x.duration, exposure_type=x.type), axis=1)
        bonds['delta_bof'] = bonds.mv * bonds.f_up
        mkt_spread_bonds = max(0., bonds.delta_bof.sum())
    else:
        mkt_spread_bonds = 0.

    if securities is not None:
        securities['f_up'] = securities.apply(lambda x: f_up(x.cc_step, x.duration, exposure_type=x.type), axis=1)
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


def f_up(cc_step: int, duration: int, exposure_type: str = 'bonds') -> float:
    """
    Factor to apply to market value in stress
    :param cc_step: maps to rating 0-6, & 7 is unrated.
    :param duration:
    :param type: bonds, ri_no_mcr, eea_covered, gov_eea ,gov_non_eea, sec_type1, sec_type2, resec
    :return:

    f = alpha + beta * (duration - duration index adjustment)
    """
    if exposure_type == 'bonds':
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
    elif exposure_type == 'ri_no_mcr':
        dur_index = int(min(duration // 5, 4))
        duration_adjustment = dur_index * 5
        alpha = np.array([0., 0.375, 0.585, 0.61, 0.635])
        beta = np.array([0.075, 0.042, 0.005, 0.005, 0.005])
        f = alpha[dur_index] + beta[dur_index] * (duration - duration_adjustment)
    elif exposure_type == 'ri_no_mcr':
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
    elif exposure_type == 'gov_eea':
        f = 0.
    elif exposure_type == 'gov_non_eea':
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
    elif exposure_type == 'sec_type1':
        beta = np.array([0.021, 0.042, 0.074, 0.085])
        f = beta[cc_step] * duration
    elif exposure_type == 'sec_type2':
        beta = np.array([0.125, 0.134, 0.166, 0.197, 0.82, 1., 1.])
        f = beta[cc_step] * duration
    elif exposure_type == 'resec':
        beta = np.array([0.33, 0.4, 0.51, 0.91, 1., 1., 1.])
        f = beta[cc_step] * duration
    return min(1., f)
