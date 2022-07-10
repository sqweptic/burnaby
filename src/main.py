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
    continuous_measure_col=None,
    nominator_col=None,
    denominator_col=None,
    is_uniq_id_proportions=False,
    na_is_zero=False,
    outliers=None,
    outliers_quantile=None,
    outliers_quantile_min_value=None,
    hypothesis=None,
    aggregation_values=None
):
    if ab_test_name in _managers:
        return _managers[ab_test_name].calc_metrics(
            name=name,
            mask=mask,
            silent=silent,
            continuous_measure_col=continuous_measure_col,
            nominator_col=nominator_col,
            denominator_col=denominator_col,
            is_uniq_id_proportions=is_uniq_id_proportions,
            outliers=outliers,
            outliers_quantile=outliers_quantile,
            outliers_quantile_min_value=outliers_quantile_min_value,
            na_is_zero=na_is_zero,
            hypothesis=hypothesis,
            aggregation_values=aggregation_values
        )
    else:
        print('no such ab test - ', ab_test_name)

def print_statistics_report(ab_test_name, correction_method='holm'):
    if ab_test_name in _managers:
        _managers[ab_test_name].print_statistics_report(correction_method)
    else:
        display('no such ab test', ab_test_name)

def save_report_to_excel(
    ab_test_name,
    filename_or_path,
    correction_method='holm'
):
    if ab_test_name in _managers:
        _managers[ab_test_name].save_report_to_excel(
            filename_or_path,
            correction_method
        )
    else:
        display('save_report_to_excel')
