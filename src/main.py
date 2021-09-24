import pandas as pd
import seaborn as sns

from abtest import _ABTest

_tests_dict = {}

def set_test(
    ab_test_name,
    data,
    groups_col,
    date_col,
    uniq_id_col,
    aggregate_cols = [],
    count_cols = []
):
    print(data)
    _tests_dict[ab_test_name] = _ABTest(
        ab_test_name,
        data,
        groups_col
    )
    print(ab_test_name)

def ab_test_validation(
    ab_test_name,
    validation_kind
):
    if validation_kind == 'avg':
        _tests_dict[ab_test_name]._display_describe_averages()
    elif validation_kind == 'all':
        _tests_dict[ab_test_name]._display_describe_averages()
        # ...

def available_statistical_hypothesis_list(ab_test_name):
    pass

def test_hypothesis(ab_test_name, hypotesis_name=None, hypotesis_id=None):
    pass

def get_compilation(ab_test_name):
    pass