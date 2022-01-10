from IPython.display import display

from ab_manager import ABManager, _ALL_VALIDATORS
from ab_consts import DEFAULT_ALPHA

_managers = {}

def set_ab_test(
    ab_test_name,
    dataframe,
    group_col,
    date_col,
    uniq_id_col,
    control_group_name = None,
    data_cols = None
):
    _managers[ab_test_name] = ABManager(
        ab_test_name,
        dataframe,
        group_col,
        date_col,
        uniq_id_col,
        control_group_name,
        data_cols
    )

    return _managers[ab_test_name]

def validate_ab_test_data(
    ab_test_name,
    validators=_ALL_VALIDATORS
):
    if ab_test_name in _managers:
        _managers[ab_test_name].validate_ab_test_data(
            validators
        )

def test_hypothesis_relational(
    ab_test_name,
    nominator,
    denominator,
    stat_test,
    description=None,
    uniq_id_rel=True,
    significance_level=DEFAULT_ALPHA
):
    display('test_hypothesis_relational')

    if ab_test_name in _managers:
        _managers[ab_test_name].test_hypothesis_relational(
            nominator,
            denominator,
            stat_test,
            description,
            uniq_id_rel,
            significance_level
        )
    else:
        display('no such ab test', ab_test_name)

def test_hypothesis_continuous(
    ab_test_name,
    value,
    stat_test,
    description=None,
    significance_level=DEFAULT_ALPHA
):
    display('test_hypothesis_continuous')
    if ab_test_name in _managers:
        _managers[ab_test_name].test_hypothesis_continuous(
            value,
            stat_test,
            description,
            significance_level
        )
    else:
        display('no such ab test', ab_test_name)

def print_statistical_report(ab_test_name):
    display('print_statistical_report')

    if ab_test_name in _managers:
        _managers[ab_test_name].print_statistical_report()
    else:
        display('no such ab test', ab_test_name)


def save_report_to_html(ab_test_name):
    display('save_report_to_html')
