import numpy as np
from IPython.display import display
from scipy.stats import ttest_ind
from statsmodels.stats.proportion import proportions_chisquare

from ab_consts import STAT_TEST_CHISQUARE
from ab_consts import STAT_TEST_TTEST
from ab_consts import STAT_TEST_TTEST_WELSH
from ab_consts import DEFAULT_ALPHA
from ab_consts import H_CONTROL_GROUP_KEY
from ab_consts import H_PVALUE_KEY
from ab_consts import H_SIGNIFICANCE_KEY
from ab_consts import H_SIGNIFICANCE_LEVEL_KEY
from ab_consts import H_TEST_GROUP_KEY


class Hypothesis:
    @staticmethod
    def generate_hypothesis_name(
        hypothesys_name,
        value_col = '',
        nom_col = '',
        den_col = ''
    ):
        return ' '.join([hypothesys_name, nom_col, den_col, value_col])

    def __init__(
        self,
        nom_col='',
        den_col='',
        value_col='',
        name = '',
        control_group_name = None,
        group_col=None,
        stat_test=None,
        combined_groups={}
    ):
        self.nom_col = nom_col
        self.den_col = den_col
        self.value_col = value_col
        self.name = name
        self.stat_test = stat_test
        self.group_col = group_col
        self.control_group_name = control_group_name
        self.combined_groups = combined_groups

        self.groups_hypothesis = {}

    def test(
        self,
        h_df,
        stat_test,
        save_testing=True,
        significance_level=DEFAULT_ALPHA
    ):
        if len(self.combined_groups.keys()) == 0:
            raise ValueError('groups combination are not set')

        _groups_hypothesis = {}
        control_df = h_df[h_df[self.group_col] == self.control_group_name]

        for combination_name, groups_combination in self.combined_groups.items():
            test_df = h_df[h_df[self.group_col] == groups_combination['test']]

            if stat_test == STAT_TEST_CHISQUARE:
                _, pvalue, _ = proportions_chisquare(
                    [
                        control_df[self.nom_col].values[0],
                        test_df[self.nom_col].values[0]
                    ],
                    [
                        control_df[self.den_col].values[0],
                        test_df[self.den_col].values[0]
                    ]
                )

                _groups_hypothesis[combination_name] = {
                    H_PVALUE_KEY: pvalue,
                    H_CONTROL_GROUP_KEY:
                        (control_df[self.nom_col] / control_df[self.den_col])\
                            .values[0],
                    H_TEST_GROUP_KEY:
                        (test_df[self.nom_col] / test_df[self.den_col])\
                            .values[0],
                    H_SIGNIFICANCE_LEVEL_KEY: significance_level,
                    H_SIGNIFICANCE_KEY: pvalue < significance_level
                }

            elif stat_test in (STAT_TEST_TTEST, STAT_TEST_TTEST_WELSH):
                if control_df[self.value_col].shape[0] > 1\
                and test_df[self.value_col].shape[0] > 1:
                    _, pvalue = ttest_ind(
                        control_df[self.value_col],
                        test_df[self.value_col],
                        equal_var=stat_test == STAT_TEST_TTEST
                    )

                    _groups_hypothesis[combination_name] = {
                        H_PVALUE_KEY: pvalue,
                        H_CONTROL_GROUP_KEY: control_df[self.value_col].mean(),
                        H_TEST_GROUP_KEY: test_df[self.value_col].mean(),
                        H_SIGNIFICANCE_LEVEL_KEY: significance_level,
                        H_SIGNIFICANCE_KEY: pvalue < significance_level
                    }
                else:
                    display(
                        'not enough data to test "' +
                        Hypothesis.generate_hypothesis_name(
                            self.name,
                            self.value_col
                        ) +
                        '" hypothesis in groups ' +
                        combination_name
                    )

                    _groups_hypothesis[combination_name] = {
                        H_PVALUE_KEY: np.NaN,
                        H_CONTROL_GROUP_KEY: np.NaN,
                        H_TEST_GROUP_KEY: np.NaN,
                        H_SIGNIFICANCE_LEVEL_KEY: significance_level,
                        H_SIGNIFICANCE_KEY: False
                    }

            if combination_name not in _groups_hypothesis:
                _groups_hypothesis[combination_name] = None

        if save_testing:
            self.groups_hypothesis = _groups_hypothesis

        return _groups_hypothesis

    def get_name(self):
        return self.name

    def get_combined_hypothesis(self):
        return self.groups_hypothesis