"""

SCR NL Cat Man-Made:
 - Fire
 - Motor
 - Liability
 - Other NL


Test data:
from tests.dummy_data import Dummy_Data as DD
dd = DD()
dd = Dummy_Data()
liab_vol = dd.liab_vol.copy()

from scr_nl.cat.manmade.manmade import get_liab_factors

Not yet prepared:
- credit
- marine
- aviation
- other NL
"""

# Standard packages:
import os
import pathlib
import numpy as np
import pandas as pd


def get_liab_factors():
    # Load the risk factors:
    fldr = pathlib.Path(__file__).parent.resolve()
    rf = pd.read_csv(os.path.join(fldr, 'factors_liab.csv'), index_col=[0]).drop(columns='group_name')
    return rf


def liab_gross_losses(liab_vol):
    vol = liab_vol.copy()
    rf = get_liab_factors()
    vol = vol.merge(rf, how='inner', left_on='grp_liab', right_index=True)
    vol['gross_loss'] = vol.gep * vol.risk_factor
    vol['no_claims'] = (vol.gross_loss / vol.limit_indem / 1.15)
    vol.no_claims = vol.no_claims.replace(np.inf, np.nan).fillna(1)
    vol['claim_amount'] = vol.gross_loss / vol.no_claims
    return vol


def liab_div_loss(losses: np.array):
    """ Diversify within grp_liab """
    fldr = pathlib.Path(__file__).parent.resolve()
    corr = pd.read_csv(os.path.join(fldr, 'corr_liab.csv'), index_col=[0])
    div_loss = np.matmul(losses.T, np.matmul(corr,losses))**0.5
    return div_loss


def liab(liab_vol, programs, covers):
    """ Main mam-made liability SCR function """
    gross_losses = liab_gross_losses(liab_vol)

    # Need full index for each group to apply correlation:
    gl = gross_losses['gross_loss'].groupby(by=['grp_liab']).sum().reindex(range(1,6)).rename('loss').fillna(0).array

    div_gross = liab_div_loss(gl)

    net_losses = manmade_liab_reinsurance(gross_losses, programs, covers)
    nl = net_losses.groupby(by='grp_liab').sum().reindex(range(1, 6)).rename('loss').fillna(0).array
    div_net = liab_div_loss(nl)
    return pd.DataFrame.from_dict({'gross_loss': div_gross, 'net_loss': div_net}, orient='index', columns=['manmade_liab']).T


def manmade_liab_reinsurance(
        gross_losses,
        programs=pd.DataFrame.from_dict({'p1': {'xol_xs': 10, 'xol_limit': 20, 'reinstatement': 0.5, 'qs': 0.6},
                                         'p2': {'xol_xs': 5, 'xol_limit': 10, 'reinstatement': 0.25, 'qs': 0.8}},
                                        'index'),
        covers=pd.DataFrame.from_dict({'DE': 'p1', 'CH': 'p1', 'PL': 'p2'}, 'index', columns=['prog_id'])
):
    """
    Simplified example to produce net losses for each county allowing for multi-country reinsurance programs
    """

    gross = gross_losses.reset_index()
    gross = gross.merge(covers, how='left', left_on='country', right_index=True)
    prog_loss = gross.groupby(['prog_id']).sum()
    prog_loss = prog_loss.merge(programs, how='left', left_on='prog_id', right_index=True)

    prog_loss['xol_rec'] = prog_loss.apply(lambda x:
                                           -min(x.xol_limit - x.xol_xs, max(0, x.gross_loss - x.xol_xs)),
                                           axis=1)
    # TODO: verify logic for reinstatement premiums on liability claims
    prog_loss['reins'] = - prog_loss.xol_rec / (prog_loss.xol_limit - prog_loss.xol_xs) * prog_loss.reinstatement
    prog_loss['net_xol'] = prog_loss[['gross_loss', 'xol_rec', 'reins']].sum(axis=1)
    prog_loss['qs_rec'] = -prog_loss.net_xol * prog_loss.qs
    prog_loss['net_loss'] = prog_loss['net_xol'] + prog_loss['qs_rec']
    prog_loss = prog_loss[['net_loss']]

    gross['prog_tot'] = gross[['gross_loss', 'prog_id']].groupby(by=['prog_id']).transform(sum)
    gross['pc_of_prog'] = gross.gross_loss/gross.prog_tot
    gross = gross.reset_index().merge(prog_loss, how='left', on=['prog_id'])
    gross.net_loss = gross.net_loss * gross.pc_of_prog
    # Filling for countries without a reinsurance program:
    gross.net_loss = gross.net_loss.fillna(gross.gross_loss)
    gross = gross.set_index(['country', 'grp_liab'])[['gross_loss', 'net_loss']].sort_index()
    return gross['net_loss']


def fire(max_prop_sum_ins: pd.Series, programs, covers):
    """
    Man-made Fire
    """
    ncr = manmade_re(max_prop_sum_ins, programs, covers)
    country_with_max = ncr.idxmax()
    gross = max_prop_sum_ins.loc[country_with_max]
    net = ncr.max()
    return pd.DataFrame.from_dict({'gross_loss': gross, 'net_loss': net}, orient='index', columns=['manmade_fire']).T


def motor(vehicles_insured: pd.DataFrame, programs, covers):
    """
    Man-made motor

    Example:
        # TODO: update example
        vehicles_insured = {'u24m': 50, 'o24m':50}
    """
    motor_scr = lambda x: 50000 * max(120,
                      (x.lim_over_24m +
                              0.05 * x.lim_below_24m +
                              0.95 * min(x.lim_below_24m, 20000))**0.5
                      )
    gross_total = motor_scr(vehicles_insured.sum())

    # Allocating gross to country:
    # TODO: refine this allcoation mechanism
    loss_by_country = vehicles_insured.sum(axis=1).rename('nveh').to_frame()
    loss_by_country['tot'] = loss_by_country['nveh'].sum()
    loss_by_country['pc_of_tot'] = loss_by_country.nveh/loss_by_country.tot
    loss_by_country['gross_loss'] = loss_by_country.pc_of_tot * gross_total
    gross = loss_by_country['gross_loss']

    net = manmade_re(gross, programs, covers)
    return pd.DataFrame.from_dict({'gross_loss': gross.sum(), 'net_loss': net.sum()}, orient='index', columns=['manmade_motor']).T

def manmade_re(
        gross_losses,
        programs=pd.DataFrame.from_dict({'p1': {'xol_xs': 10, 'xol_limit': 20, 'reinstatement': 0.5, 'qs': 0.6},
                                         'p2': {'xol_xs': 5, 'xol_limit': 10, 'reinstatement': 0.25, 'qs': 0.8}},
                                        'index'),
        covers=pd.DataFrame.from_dict({'DE': 'p1', 'CH': 'p1', 'PL': 'p2'}, 'index', columns=['prog_id'])
):
    """
    Simplified example to produce net losses for each county allowing for multi-country reinsurance programs
    """

    gross = gross_losses.reset_index()
    gross = gross.merge(covers, how='left', left_on='country', right_index=True)
    prog_loss = gross.groupby(['prog_id']).sum()
    prog_loss = prog_loss.merge(programs, how='left', left_on='prog_id', right_index=True)

    prog_loss['xol_rec'] = prog_loss.apply(lambda x:
                                           -min(x.xol_limit - x.xol_xs, max(0, x.gross_loss - x.xol_xs)),
                                           axis=1)
    # TODO: verify logic for reinstatement premiums on manmade claims
    prog_loss['reins'] = - prog_loss.xol_rec / (prog_loss.xol_limit - prog_loss.xol_xs) * prog_loss.reinstatement
    prog_loss['net_xol'] = prog_loss[['gross_loss', 'xol_rec', 'reins']].sum(axis=1)
    prog_loss['qs_rec'] = -prog_loss.net_xol * prog_loss.qs
    prog_loss['net_loss'] = prog_loss['net_xol'] + prog_loss['qs_rec']
    prog_loss = prog_loss[['net_loss']]

    gross['prog_tot'] = gross[['gross_loss', 'prog_id']].groupby(by=['prog_id']).transform(sum)
    gross['pc_of_prog'] = gross.gross_loss/gross.prog_tot
    gross = gross.reset_index().merge(prog_loss, how='left', on=['prog_id'])
    gross.net_loss = gross.net_loss * gross.pc_of_prog
    # Filling for countries without a reinsurance program:
    gross.net_loss = gross.net_loss.fillna(gross.gross_loss)
    gross = gross.set_index(['country'])[['gross_loss', 'net_loss']].sort_index()
    return gross['net_loss']
