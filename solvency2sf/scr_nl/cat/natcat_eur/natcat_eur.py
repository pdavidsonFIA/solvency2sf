"""
natcat_eur

This more-or-less replicates the calculations in the Lloyd's template.

Cresta zone weighting:
- input sums insured by cresta region, hazard, risk
- appply risk weights based on cresta region
- apply factor based on risk type (motor, fire...)
- diversify using correlations for cresta regions and hazard
>> This provides volume measures per hazard and country

Now:
- apply risk factor based on cause of loss (windstorm, earthquake)
- Calculate loss in each scenarios for each loss event (may be more than one)
~~ This is  a different calculation order to the Lloyds template to enable aggegation of cat losses accross country
~~ and apply reinsurance mitigation prior to diversifying
>> Now have gross losses for each hazard/scenario/country

These gross losses can be aggregated according to a company specific reinsurance program,
- apply mitigation, and
- allocate back to countries, giving
>> Net losses for each hazard/scenario/country

Apply diversification between countries:
- using corr matrices

Choose scenario giving max loss after reinsurance

Test data:

import pandas as pd
import numpy as np
import math

hazards = ['windstorm', 'earthquake', 'flood', 'hail']
risks = ['fire', 'mat', 'motor']
countries = ['DE', 'CH', 'PL']
zones = range(1,100)
idx = pd.MultiIndex.from_product((hazards,risks, countries, zones), names = ['hazard', 'risk', 'country_isocode', 'riskregion'])
sumsinsured = pd.DataFrame(index=idx).sort_index()
sumsinsured.loc[pd.IndexSlice['windstorm',['fire', 'mat'], 'DE', 1:95], 'suminsured']=200
sumsinsured.loc[pd.IndexSlice['earthquake',['fire', 'mat'], 'DE',1:95], 'suminsured']=200
sumsinsured.loc[pd.IndexSlice[['flood', 'hail'],:, 'DE'], 'suminsured']=200

sumsinsured.loc[pd.IndexSlice['windstorm',['fire', 'mat'], 'CH', 1:26], 'suminsured']=100
sumsinsured.loc[pd.IndexSlice['earthquake',['fire', 'mat'], 'CH', 1:26], 'suminsured']=100
sumsinsured.loc[pd.IndexSlice[['flood', 'hail'],:, 'CH', 1:26], 'suminsured']=100

sumsinsured.loc[pd.IndexSlice['windstorm',['fire', 'mat'], 'PL'], 'suminsured']=100
sumsinsured.loc[pd.IndexSlice['flood',:, 'PL'], 'suminsured']=100
sumsinsured = sumsinsured.dropna()

from scr_nl.cat.natcat_eur.natcat_eur import cresta_volumes, div_within_region, specified_loss, scenario_losses
from scr_nl.cat.natcat_eur.natcat_eur import get_scenarios, example_reinsurance
sl = specified_loss(sumsinsured)
gross = scenario_losses(sl)
net = example_reinsurance(gross)

from scr_nl.cat.natcat_eur.natcat_eur import diversify_between_countries, natcat_agg
gross_x = diversify_between_countries(gross)
net_x = diversify_between_countries(net)
natcat = natcat_agg(gross_x, net_x)

"""

# Standard packages:
import pandas as pd
import numpy as np
import math
import os
import glob
import importlib.resources


### Functions which just load parameters ###

def get_risk_weights():
    """ Reads the risk_weights csv's into a dataframe """
    natcat_risks = ['windstorm', 'earthquake', 'flood', 'hail', 'subsidence']
    # Load natcat cresta risk weights:
    with importlib.resources.path(__package__, 'risk_weights') as p:
        rw_path = p
    rw = []
    for risk in natcat_risks:
        rw_file = os.path.join(rw_path, risk + '.csv')
        rw.append(pd.read_csv(rw_file, index_col=0).unstack().dropna().rename(risk))
    risk_weights = pd.concat(rw, axis=1).rename_axis(['country_isocode', 'riskregion'])
    return risk_weights


def get_risks_corr_mat():
    """
    Returns a dictionary of correlation matrices (between countries)
    Keys:
    - risk
    :return:
    """
    natcat_risks = ['windstorm', 'earthquake', 'flood', 'hail', 'subsidence']
    corr = {}
    with importlib.resources.path(__package__, 'corr') as p:
        corr_path = p
    for risk in natcat_risks:
         file = os.path.join(corr_path, risk + '.csv')
         corr[risk] = pd.read_csv(file, index_col=0)
    return corr


def get_cresta_corr_mat():
    """
    Returns a nested dictionary of every correlation matrix
    Keys:
     - hazard
     - country
     Loads every corrmat for every country - this could be optimised.
    """
    natcat_risks = ['windstorm', 'earthquake', 'flood', 'hail', 'subsidence']

    with importlib.resources.path(__package__, 'corr_cresta') as p:
        corr_mat_fldr = p
    corr_cresta = {}
    for risk in natcat_risks:
        corr_cresta[risk] = {}
        for file in glob.glob(os.path.join(corr_mat_fldr, risk + '*.csv')):
            country = os.path.splitext(file)[0].split('_')[-1]
            corr_cresta[risk][country] = pd.read_csv(file, index_col=0)
    return corr_cresta


def get_scenarios():
    with importlib.resources.open_text(__package__, 'scenarios.csv') as f:
        scenarios = pd.read_csv(f, index_col=[0, 1])
    return scenarios


def get_sl_factors():
    # Load the specified loss factors:
    with importlib.resources.open_text(__package__, 'specified_loss.csv') as f:
        sl = pd.read_csv(f, index_col=[0]).drop(columns='country')
    return sl


### Functions carrying out calculations ###


def cresta_volumes(sumsinsured):
    """
    inputs:
    - sums insured
    index:
    - hazard i.e. fire mat motor
    - country_isocode
    - cresta riskregion
    """
    si = sumsinsured.copy()

    # add the risk factors:
    with importlib.resources.open_text(__package__, 'factors.csv') as f:
        factors = pd.read_csv(f, index_col=[0])

    si = si.merge(factors.stack().rename('risk_weights'), how='left', left_on=['hazard', 'risk'], right_index=True)

    # Apply the risk risk_weights using numpy matrix multiplication:
    si['weight'] = si.suminsured * si.risk_weights
    si = si['weight'].groupby(by=['country_isocode', 'riskregion', 'hazard']).sum()
    si = si.unstack()

    # Apply risk weights:
    risk_weights = get_risk_weights()
    res = si * risk_weights

    # dropna where risk weights not defined
    res = res.dropna(axis=0, how='all')

    # This is now a full table of weighted risks by country & cresta zone
    res = res.reindex(risk_weights.index).fillna(0)
    return res


def diversify_with_corrmat(x, corr=None):
    if corr is None:
        return 0
    else:
        corr_arr = np.array(corr)
        # This is a bodge: zones not consistently defined between risk weights, correlation matrices
        v = np.array(x.loc[:len(corr.index)].fillna(0))
        # v = np.array(x.loc[corr.index].fillna(0))
        return math.sqrt(np.matmul(v.T, np.matmul(corr_arr, v)))


def div_within_region(cv):
    natcat_risks = ['windstorm', 'earthquake', 'flood', 'hail', 'subsidence']
    correlations = get_cresta_corr_mat()
    # TODO: Hate this loop, must be a better way...
    df = pd.DataFrame()
    for country in cv.index.get_level_values('country_isocode').drop_duplicates():
        for risk in natcat_risks:
            df.loc[country, risk] = diversify_with_corrmat(cv.loc[country, risk], correlations[risk].get(country))
    return df


def specified_loss(sumsinsured: pd.DataFrame):
    """
    Returns gross specified loss for each country and hazard
    """
    # Volumes for each risk factor by cresta region
    cv = cresta_volumes(sumsinsured)
    cv_div = div_within_region(cv)
    sl = get_sl_factors()

    spec_loss = cv_div * sl

    return spec_loss


def scenario_losses(spec_loss):
    # Calculate the losses in each scenario:
    sl = spec_loss.stack()
    sl.index.names = ['country_isocode', 'hazard']
    scenarios = get_scenarios().stack()
    scenarios.index.names = ['scenario', 'loss_event', 'hazard']
    losses = scenarios * sl
    return losses.rename('gross_loss')


def natcat_reinsurance(
        scen_loss,
        programs=pd.DataFrame.from_dict({'p1': {'xol_xs': 10, 'xol_limit': 20, 'reinstatement': 0.5, 'qs': 0.6},
                                         'p2': {'xol_xs': 5, 'xol_limit': 10, 'reinstatement': 0.25, 'qs': 0.8}},
                                        'index'),
        covers=pd.DataFrame.from_dict({'DE': 'p1', 'CH': 'p1', 'PL': 'p2'}, 'index', columns=['prog_id'])
):
    """
    Simplified example to produce net losses for each county allowing for multi-country reinsurance programs
    """

    gross = scen_loss.to_frame()
    gross = gross.merge(covers,how='left', left_on='country_isocode', right_index=True)
    prog_loss = gross.groupby(['hazard', 'scenario', 'loss_event', 'prog_id']).sum()
    prog_loss = prog_loss.merge(programs, how='left', left_on='prog_id', right_index=True)

    prog_loss['xol_rec'] = prog_loss.apply(lambda x:
                                           -min(x.xol_limit - x.xol_xs, max(0, x.gross_loss - x.xol_xs)),
                                           axis=1)
    prog_loss['reins'] = - prog_loss.xol_rec / (prog_loss.xol_limit - prog_loss.xol_xs) * prog_loss.reinstatement
    prog_loss['net_xol'] = prog_loss[['gross_loss', 'xol_rec', 'reins']].sum(axis=1)
    prog_loss['qs_rec'] = -prog_loss.net_xol * prog_loss.qs
    prog_loss['net_loss'] = prog_loss['net_xol'] + prog_loss['qs_rec']
    prog_loss = prog_loss[['net_loss']]

    gross['prog_tot'] = gross.groupby(by=['hazard', 'scenario', 'loss_event', 'prog_id']).transform(sum)
    gross['pc_of_prog'] = gross.gross_loss/gross.prog_tot
    gross = gross.reset_index().merge(prog_loss, how='left', on=['hazard', 'scenario', 'loss_event', 'prog_id'])
    gross.net_loss = gross.net_loss * gross.pc_of_prog
    # Filling for countries without a reinsurance program:
    gross.net_loss = gross.net_loss.fillna(gross.gross_loss)
    gross = gross.set_index(['hazard', 'scenario', 'loss_event', 'country_isocode'])[['gross_loss', 'net_loss']].sort_index()
    return gross['net_loss']


def diversify_between_countries(scen_loss):
    """
    scen_loss is indexed by:
    - hazard
    - scenario
    - loss event
    Returns:
        - loss for each scenario & loss event (a/b, 1/2)
        - for each hazard
        - diversified within countries
    """
    correlations = get_risks_corr_mat()
    hazards = ['windstorm', 'earthquake', 'flood', 'hail', 'subsidence']
    sc = []
    for haz in hazards:
        #haz = 'windstorm'
        # build a series for each hazard, makes easier for matmul (series not equal lengths)
        sx = scen_loss.loc[haz]
        sx = sx.unstack('country_isocode')
        # Sort the index alphabetically in corr mat:
        corr = correlations[haz].sort_index()
        corr = corr[corr.index]
        sc.append(sx.apply(lambda x: math.sqrt(np.matmul(x, np.matmul(corr, x.T))), axis=1).rename(haz))
    sc = pd.concat(sc, axis=1)
    return sc


def natcat_agg(gross_x, net_x):
    """ Select the biting scenario for each loss event """
    net_loss = net_x.groupby('scenario').sum()
    gross_loss = gross_x.groupby('scenario').sum()
    biting_scenario = net_loss.idxmax().rename('scenario')
    gx = gross_loss.apply(lambda x: x.loc[biting_scenario[x.name]]).rename('gross_loss')
    nx = net_loss.apply(lambda x: x.loc[biting_scenario[x.name]]).rename('net_loss')
    losses = pd.concat((gx, nx), axis=1)
    natcat_scr_div = (losses**2).sum().apply(math.sqrt)
    return natcat_scr_div
