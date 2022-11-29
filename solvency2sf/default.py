"""
SCR Default

Test data:
from s2sf_tests.dummy_data import Dummy_Data
dd = Dummy_Data()

## test type 1 default SCR
type_1 = dd.type_1.copy()
scr_default_t1 = scr_def_t1(type_1)
scr_default_t1
# comparison with expected
scr_default_t1 == dd.scr_def_t1_expected

## test type 2 default SCR
type_2 = dd.type_2.copy()
scr_default_t2 = scr_def_t2(type_2)
scr_default_t2
# comparison with expected
scr_default_t2 == dd.scr_def_t2_expected

## test of aggregation
scr_def = scr_def_agg(scr_default_t1, scr_default_t2)
scr_def
# comparison with expected
scr_def == dd.scr_def_expected


"""

import pandas as pd


def scr_def(type1, type2):
    # Directive 2015/35

    # Article 200 & 201
    scr_default_t1, type1_details = scr_def_t1(type1)
    # Article 202
    scr_default_t2 = scr_def_t2(type2)
    # Article 189.1
    scr_default = scr_def_agg(scr_default_t1, scr_default_t2)

    return scr_default, scr_default_t1, scr_default_t2, type1_details


def scr_def_t1(type1):
    # Directive 2015/35
    # Floor the values at 0 i.e. no negative balances:
    type1.balance = type1.balance.apply(lambda x: max(x, 0))

    # TODO: merge loss rates from a table
    type1.loc[type1.category == 3, 'loss_rate'] = 1
    # rec.loc[pd.IndexSlice[1, :, 2], 'loss_rate'] = 0.9
    type1.loc[type1.category == 1, 'loss_rate'] = 0.5

    # Article 192 Loss given default:
    type1['lgd'] = type1.loss_rate * (type1.balance + 0.5 * type1.mitigation)
    type1.lgd = type1.lgd.astype(float)
    type1['lgd2'] = type1.lgd ** 2

    # Article 201
    type1g = type1.groupby(by='rating').sum()[['lgd', 'lgd2']]

    # Article 199
    default_probs = pd.DataFrame([0.00002, 0.0001, 0.0005, 0.0024, 0.012, 0.042, 0.042], index=range(7),
                                 columns=['prob_def'])
    type1g = type1g.merge(default_probs, how='left', left_index=True, right_index=True)
    type1 = type1.merge(default_probs, how='left', left_on='rating', right_index=True)

    v_inter = 0
    lgd = type1g.lgd.array
    dp = type1g.prob_def.array
    for j in range(len(type1g)):
        for k in range(len(type1g)):
            v_inter += dp[j] * (1 - dp[j]) * dp[k] * (1 - dp[k]) / (1.25 * (dp[j] + dp[k]) - dp[j] * dp[k]) * lgd[j] * \
                       lgd[k]

    v_intra = 0
    lgd2 = type1g.lgd2.array
    for j in range(len(type1g)):
        v_intra += 1.5 * dp[j] * (1 - dp[j]) / (2.5 - dp[j]) * lgd2[j]

    # Article 201
    v_type1 = v_intra + v_inter
    # Article 200.4
    sd_type1 = (v_type1) ** 0.5
    total_lgd = type1g.lgd.sum()

    # Article 200
    sd_to_lgd = sd_type1 / total_lgd
    # Article 200.1
    if sd_to_lgd <= 0.07:
        t1 = 3 * sd_type1
    # Article 200.2
    elif 0.07 < sd_to_lgd <= 0.2:
        t1 = 5 * sd_type1
    # Article 200.3
    else:
        t1 = total_lgd
    type1_details=type1
    return t1,type1_details


def scr_def_t2(type2):
    # Directive 2015/35
    # Article 202
    t2 = 0.9 * type2.loc['overdue_more3m', 'balance'] + 0.15 * type2.loc['other', 'balance']
    return t2


def scr_def_agg(scr_def_t1, scr_def_t2):
    # Directive 2015/35
    # Article 189.1
    default = (scr_def_t1 ** 2 + 1.5 * scr_def_t1 * scr_def_t2 + scr_def_t2 ** 2) ** 0.5
    return default
