import numpy as np
import pandas as pd
import pathlib


def scr_mkt_conc(asset_list: pd.DataFrame) -> pd.DataFrame:
    """

    :param asset_list:
    :return:
    """
    # Total amount of assets considered in this module:
    assets_xl = asset_list.exposure.sum()

    conc_factors = pd.read_csv(pathlib.Path(__file__).parent.joinpath('conc_factors.csv'), index_col=[0,1])
    df = asset_list.merge(conc_factors, on=["exposure_type", "cc_step"], how="left")

    # Credit quality step 7 is unrated
    credit_threshold = {0: 0.03, 1: 0.03, 2: 0.03, 3: 0.015, 4: 0.015, 5: 0.015, 6: 0.015, 7: 0.015}
    # Relative excess exposure threshold
    df['ct'] = df.cc_step.map(credit_threshold)

    df.exposure = df.exposure.fillna(0.)
    df["xs_exposure"] = df.apply(lambda x: max(0., x.exposure/assets_xl - x.ct), axis=1)

    df['Conc'] = df.xs_exposure * df.gi * df.assets_xl
    mkt_conc = np.square(df.Conc).sum()**0.5

    return mkt_conc