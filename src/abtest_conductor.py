import pandas as pd
import seaborn as sns

from abtest import _ABTest


VALIDATION_TYPE__GROUPS_PER_UNIQ_ID = 'groups_per_uniq_id'
_ALL_VALIDATORS = [
    VALIDATION_TYPE__GROUPS_PER_UNIQ_ID
]

class ABTestConductor:
    def __init__(
        self,
        ab_test_name,
        dataframe,
        group_col,
        date_col,
        uniq_id_col,
        control_group_name = '',
        aggregate_cols = [],
        data_cols = None
    ) -> None:
        self.abtest = _ABTest(
            ab_test_name,
            dataframe,
            group_col,
            date_col,
            uniq_id_col,
            control_group_name = '',
            aggregate_cols = [],
            data_cols = None
        )

    def validate_ab_test_data(self, validators = _ALL_VALIDATORS):
        self.abtest._display_describe()

        if VALIDATION_TYPE__GROUPS_PER_UNIQ_ID in validators:
            self.abtest._display_describe()

    def test_hypothesis_rational(
        self,
        nominator,
        denominator,
        stat_test,
        description
    ):
        pass