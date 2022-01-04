from IPython.display import display

from abtest import _ABTest
from abtest_conductor import ABTestConductor, _ALL_VALIDATORS, VALIDATION_TYPE__GROUPS_PER_UNIQ_ID

_conductors = {}

def set_ab_test(
    ab_test_name,
    dataframe,
    group_col,
    date_col,
    uniq_id_col,
    control_group_name = '',
    aggregate_cols = [],
    data_cols = None
):
    _conductors[ab_test_name] = ABTestConductor(
        ab_test_name,
        dataframe,
        group_col,
        date_col,
        uniq_id_col,
        control_group_name,
        aggregate_cols,
        data_cols
    )

    return _conductors[ab_test_name]

def validate_ab_test_data(
    ab_test_name,
    validators=_ALL_VALIDATORS
):
    if ab_test_name in _conductors:
        _conductors[ab_test_name].validate_ab_test_data(
            validators
        )

def test_hypothesis_rational(
    ab_test_name,
    nominator,
    denominator,
    stat_test,
    description=None
):
    display('test_hypothesis_rational')
    if ab_test_name in _conductors:
        _conductors[ab_test_name].test_hypothesis_rational(
            nominator,
            denominator,
            stat_test,
            description
        )
    else:
        display('no such ab test')

def test_hypothesis_continuous(
    ab_test_name,
    value,
    stat_test,
    description=None
):
    display('test_hypothesis_continuous')

def print_statistical_report(ab_test_name):
    display('print_statistical_report')

def save_report_to_html(ab_test_name):
    display('save_report_to_html')
