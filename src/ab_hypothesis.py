import hashlib
from itertools import combinations

from IPython.display import display
from scipy.stats import ttest_ind
from statsmodels.stats.proportion import proportions_chisquare

from ab_consts import STAT_TEST_CHISQUARE
from ab_consts import STAT_TEST_TTEST, STAT_TEST_TTEST_WELSH

class Hypothesis:
    @staticmethod
    def generate_hypothesis_name(hypothesys_name, value_col = '', nom_col = '', den_col = ''):
        return hypothesys_name + nom_col + den_col + value_col

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
        print(combined_groups)
        self.combined_groups = combined_groups

        self.groups_hypothesis = {}

    def test(self, h_df, stat_test):
        display(h_df)

        if len(self.combined_groups.keys()) == 0:
            display('error')
            return

        display('here1', self.combined_groups)
        for combination_name, groups_combination in self.combined_groups.items():
            display('here', self.group_col, groups_combination['control'])
            display(h_df[self.group_col])

            control_df = h_df[h_df[self.group_col] == groups_combination['control']]
            test_df = h_df[h_df[self.group_col] == groups_combination['test']]

            if stat_test == STAT_TEST_CHISQUARE:
                _, pvalue, _ = proportions_chisquare(
                    [control_df[self.nom_col].iloc[0], test_df[self.nom_col].iloc[0]],
                    [control_df[self.den_col].iloc[0], test_df[self.den_col].iloc[0]]
                )

                self.groups_hypothesis[combination_name] = pvalue

            elif stat_test in (STAT_TEST_TTEST, STAT_TEST_TTEST_WELSH):
                _, pvalue = ttest_ind(control_df[self.value_col], test_df[self.value_col])

                self.groups_hypothesis[combination_name] = pvalue
            else:
                self.groups_hypothesis[combination_name] = None

        display(self.groups_hypothesis)
