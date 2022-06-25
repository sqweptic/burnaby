import numpy as np
import pandas as pd

from IPython.display import display

from scipy.stats import ttest_ind
from statsmodels.stats.proportion import proportions_chisquare

from ab_consts import STAT_TEST_CHISQUARE
from ab_consts import STAT_TEST_TTEST
from ab_consts import STAT_TEST_TTEST_WELSH
from ab_consts import DEFAULT_SIGNIFICANCE_LEVEL
from ab_consts import H_CONTROL_GROUP_KEY
from ab_consts import H_PVALUE_KEY
from ab_consts import H_SIGNIFICANCE_KEY
from ab_consts import H_SIGNIFICANCE_LEVEL_KEY
from ab_consts import H_TEST_GROUP_KEY


class ABHypothesis:
    @staticmethod
    def generate_hypothesis_name(
        hypothesys_name,
        value_col = ''
    ):
        return ' '.join([hypothesys_name, value_col])

    def __init__(
        self,
        name = '',
        nominator_col=None,
        denominator_col=None,
        continuous_measure_col=None,
        control_group_name=None,
        group_col=None,
        combined_groups={},
        stat_test=None,
        significance_level=DEFAULT_SIGNIFICANCE_LEVEL
    ):
        self.nominator_col = nominator_col
        self.denominator_col = denominator_col
        self.continuous_measure_col = continuous_measure_col
        self.name = name
        self.group_col = group_col
        self.control_group_name = control_group_name
        self.combined_groups = combined_groups
        self.stat_test = stat_test
        self.significance_level=significance_level

    def get_significance_level(self):
        return self.significance_level

    def _get_empty_data(self, combination_name):
        empty_h_df = pd.DataFrame()

        empty_h_df.loc[combination_name, H_PVALUE_KEY] = np.NaN
        empty_h_df.loc[combination_name, H_SIGNIFICANCE_LEVEL_KEY] = \
            self.significance_level
        empty_h_df.loc[combination_name, H_SIGNIFICANCE_KEY] = \
            np.NaN

        return empty_h_df

    def test(
        self,
        m_df,
        save_testing=True
    ):
        if len(self.combined_groups.keys()) == 0:
            raise ValueError('groups combination are not set')

        control_df = m_df[m_df.index == self.control_group_name]

        h_df = pd.DataFrame()

        for combination_name, groups_combination in \
            self.combined_groups.items():

            if groups_combination['test'] not in m_df.index:
                continue

            test_df = m_df[m_df.index == groups_combination['test']]

            if self.stat_test == STAT_TEST_CHISQUARE:
                c_successes = control_df[self.nominator_col].values[0]
                t_successes = test_df[self.nominator_col].values[0]
                c_trials = control_df[self.denominator_col].values[0]
                t_trials = test_df[self.denominator_col].values[0]

                if c_trials > 0 and t_trials > 0 \
                    and c_successes > 0 and t_successes > 0:
                    _, pvalue, _ = proportions_chisquare(
                        [
                            c_successes,
                            t_successes
                        ],
                        [
                            c_trials,
                            t_trials
                        ]
                    )
                else:
                    display(
                        'zero trials or successes, hypothesis won\'t be tested'
                            + ' in groups ' + combination_name,
                        'successes in control = ' + str(c_successes),
                        'trials in control = ' + str(c_trials),
                        'successes in test = ' + str(t_successes),
                        'trials in test = ' + str(t_trials),
                    )
                    pvalue = np.NaN

                h_df.loc[combination_name, H_PVALUE_KEY] = pvalue
                h_df.loc[combination_name, H_SIGNIFICANCE_LEVEL_KEY] = \
                    self.significance_level
                h_df.loc[combination_name, H_SIGNIFICANCE_KEY] = \
                    pvalue < self.significance_level

            elif self.stat_test in (STAT_TEST_TTEST, STAT_TEST_TTEST_WELSH):
                if control_df[self.continuous_measure_col].shape[0] > 1\
                and test_df[self.continuous_measure_col].shape[0] > 1:

                    _, pvalue = ttest_ind(
                        control_df[self.continuous_measure_col],
                        test_df[self.continuous_measure_col],
                        equal_var=self.stat_test == STAT_TEST_TTEST
                    )

                    h_df.loc[combination_name, H_PVALUE_KEY] = pvalue
                    h_df.loc[combination_name, H_SIGNIFICANCE_LEVEL_KEY] = \
                        self.significance_level
                    h_df.loc[combination_name, H_SIGNIFICANCE_KEY] = \
                        pvalue < self.significance_level
                else:
                    display(
                        'not enough data to test "' +
                        ABHypothesis.generate_hypothesis_name(
                            self.name,
                            self.continuous_measure_col
                        ) +
                        '" hypothesis in groups ' +
                        combination_name
                    )

                    h_df.append(self._get_empty_data(combination_name))

        if save_testing:
            self.h_df = h_df

        return h_df

    def get_test(self):
        return self.h_df.T

    def get_name(self):
        return self.name

    # def get_combined_hypothesis(self):
    #     return self.groups_hypothesis