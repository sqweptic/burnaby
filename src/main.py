from IPython.display import display

from ab_manager import ABManager, _ALL_VALIDATORS


_managers = {}

def set_ab_test(
    ab_test_name,
    dataframe,
    abgroup_col,
    date_col,
    uniq_id_col,
    control_group_name=None,
    data_cols=None,
    significance_level=None,
    aggregations=None
):
    _managers[ab_test_name] = ABManager(
        ab_test_name,
        dataframe,
        abgroup_col,
        date_col,
        uniq_id_col,
        control_group_name,
        data_cols,
        significance_level=significance_level,
        aggregations=aggregations
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

def calc_metrics(
    ab_test_name,
    name,
    mask=None,
    silent=False,
    continue_measure_col=None,
    nominator_col=None,
    denominator_col=None,
    is_uniq_id_proportions=False,
    na_is_zero=False,
    hypothesis=None,
    aggregation_values=None
):
    print('main', 'calc_metrics')
    if ab_test_name in _managers:
        return _managers[ab_test_name].calc_metrics(
            name,
            mask,
            silent,
            continue_measure_col,
            nominator_col,
            denominator_col,
            is_uniq_id_proportions,
            na_is_zero,
            hypothesis,
            aggregation_values
        )
    else:
        print('no such ab test - ', ab_test_name)


def test_hypothesis_proportions(
    ab_test_name,
    nominator,
    denominator,
    stat_test,
    description=None,
    uniq_id_rel=True,
    significance_level=None
):
    display('test_hypothesis_proportions')

    if ab_test_name in _managers:
        _managers[ab_test_name].test_hypothesis_proportions(
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
    significance_level=None
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

def print_statistics_report(ab_test_name, correction_method='holm'):
    if ab_test_name in _managers:
        _managers[ab_test_name].print_statistics_report(correction_method)
    else:
        display('no such ab test', ab_test_name)

def save_report_to_excel(ab_test_name):
    display('save_report_to_excel')
