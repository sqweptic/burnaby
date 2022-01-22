import pandas as pd
import numpy as np
import seaborn as sns

from statsmodels.stats.multitest import multipletests

import matplotlib.pyplot as plt

from IPython.display import display

from ab_hypothesis import Hypothesis
from ab_consts import METRIC_COL_NAME
from ab_consts import DEFAULT_GROUP_NAMES
from ab_consts import H_CONTROL_GROUP_KEY
from ab_consts import H_PVALUE_KEY
from ab_consts import H_SIGNIFICANCE_KEY
from ab_consts import H_TEST_GROUP_KEY
from ab_consts import DEFAULT_SIGNIFICANCE_LEVEL


VALIDATION_TYPE__GROUPS_PER_UNIQ_ID = 'groups_per_uniq_id'
_ALL_VALIDATORS = [
    VALIDATION_TYPE__GROUPS_PER_UNIQ_ID
]

class ABManager:
    def __init__(
        self,
        ab_test_name,
        ab_df,
        abgroup_col,
        timeseries_col,
        uniq_id_col,
        control_group_name=None,
        data_cols=None,
        significance_level=None
    ):
        self.name = ab_test_name
        self.abgroup_col = abgroup_col
        self.timeseries_col = timeseries_col
        self.uniq_id_col = uniq_id_col

        self.available_groups = np.sort(ab_df[abgroup_col].unique())

        self.control_group_name = None
        if control_group_name is not None:
            if control_group_name in self.available_groups:
                self.control_group_name = control_group_name
        else:
            for group_in_ab_data in self.available_groups:
                if group_in_ab_data in DEFAULT_GROUP_NAMES:
                    self.control_group_name = group_in_ab_data

        if self.control_group_name is None:
            raise ValueError(
                'control group name is undefined or not in dataframe'
            )

        self.uniq_id_grouping_cols = [abgroup_col, timeseries_col, uniq_id_col]

        if data_cols is None:
            data_cols = np.setdiff1d(
                ab_df.columns,
                self.uniq_id_grouping_cols
            )

        self.ab_df = ab_df\
            .groupby(
                self.uniq_id_grouping_cols,
                as_index=False
            )[data_cols]\
            .sum()\

        self.ab_df[timeseries_col] = pd.to_datetime(self.ab_df[timeseries_col])

        self.ab_df.sort_values(timeseries_col, inplace=True)

        self.timeseries_period_dates = \
            np.sort(self.ab_df[timeseries_col].dt.date.unique())
        self.timeseries_period_start_date = self.timeseries_period_dates.min()

        if significance_level is not None:
            self.significance_level = significance_level

        self._hypothesis = {}
        self._combined_groups = self._pair_groups(ab_df)

    def _pair_groups(self, h_df):
        combined_groups = {}
        for group in np.sort(h_df[self.abgroup_col].unique()):
            if not group or group == self.control_group_name:
                continue

            combination_name = str(self.control_group_name) + '-' + str(group)
            combined_groups[combination_name] = {
                'control': self.control_group_name,
                'test': group
            }

        return combined_groups

    def validate_ab_test_data(self, validators = _ALL_VALIDATORS):
        display(self._describe_by_group(self.ab_df))

        if VALIDATION_TYPE__GROUPS_PER_UNIQ_ID in validators:
            display(self._get_groups_stats(self.ab_df))

    def _get_groups_stats(self, df_w_test_groups):
        return df_w_test_groups\
            .groupby(self.uniq_id_col, as_index=False)[self.abgroup_col]\
            .nunique()\
            .groupby(self.abgroup_col, as_index=False)[self.uniq_id_col]\
            .nunique()

    def _describe_by_group(self, df_to_desc):
        return df_to_desc.groupby(self.abgroup_col).describe().T

    def test_hypothesis_continuous(
        self,
        value_col,
        stat_test,
        description,
        na_is_zero=True,
        significance_level=None,
        silent=False
    ):
        h_name = Hypothesis.generate_hypothesis_name(
            description,
            value_col=value_col
        )

        if significance_level is None:
            significance_level = self.significance_level

        if h_name in self._hypothesis:
            h = self._hypothesis[h_name]
        else:
            h = Hypothesis(
                value_col=value_col,
                name=description,
                stat_test=stat_test,
                group_col=self.abgroup_col,
                control_group_name=self.control_group_name,
                combined_groups=self._combined_groups,
                significance_level=significance_level
            )
            self._hypothesis[h_name] = h

        hypothesis_df = self.ab_df

        if na_is_zero:
            hypothesis_df[value_col] = hypothesis_df[value_col].fillna(0)
        else:
            hypothesis_df = hypothesis_df[~hypothesis_df[value_col].isna()]

        hypothesis_df = hypothesis_df\
            .groupby(self.uniq_id_grouping_cols, as_index=False)[value_col]\
            .sum()

        if not silent:
            timeseries_df = hypothesis_df\
                .groupby([self.abgroup_col, self.timeseries_col], as_index=False)\
                .agg(metric = (value_col, 'mean'))

            display(
                hypothesis_df\
                    .groupby(
                        [self.abgroup_col],
                        as_index=False
                    )\
                    .agg(metric = (value_col, 'mean'))
            )

            self._draw_metrics_chart_by_timeline(
                timeseries_df,
                METRIC_COL_NAME,
                description
            )

            periods_df = self._get_testing_df_by_periods(
                hypothesis_df,
                grouping_cols=[self.abgroup_col, self.uniq_id_col],
                agg_cols=[value_col],
                agg_funcs={value_col: 'sum'},
                hypothesis=h
            )

            self._draw_metrics_chart_by_timeline_and_fill_between(
                periods_df,
                H_PVALUE_KEY,
                title=description,
                acceptance_band=1-significance_level
            )

        h.test(
            hypothesis_df,
            save_testing=True
        )

    def test_hypothesis_relational(
        self,
        nominator,
        denominator,
        stat_test,
        description,
        uniq_id_rel = False,
        significance_level=DEFAULT_SIGNIFICANCE_LEVEL,
        silent=False
    ):
        h_name = Hypothesis.generate_hypothesis_name(
            description,
            nom_col=nominator,
            den_col=denominator
        )

        if significance_level is None:
            significance_level = self.significance_level

        if h_name in self._hypothesis:
            h = self._hypothesis[h_name]
        else:
            h = Hypothesis(
                nom_col=nominator,
                den_col=denominator,
                name=description,
                stat_test=stat_test,
                group_col=self.abgroup_col,
                control_group_name=self.control_group_name,
                combined_groups=self._combined_groups,
                significance_level=significance_level
            )
            self._hypothesis[h_name] = h

        if uniq_id_rel:
            timeseries_df = self.ab_df\
                .groupby(
                    [self.abgroup_col, self.timeseries_col],
                    as_index=False
                )[[nominator, denominator]]\
                .agg({
                    nominator: lambda x: 1 if (x > 0).any() else 0,
                    denominator: lambda x: 1 if (x > 0).any() else 0
                })
        else:
            timeseries_df = self.ab_df\
                .groupby(
                    [self.abgroup_col, self.timeseries_col],
                    as_index=False
                )[[nominator, denominator]]\
                .agg({
                    nominator: lambda x: sum(x) if (x > 0).any() else 0,
                    denominator: lambda x: sum(x) if (x > 0).any() else 0
                })

        timeseries_df[METRIC_COL_NAME] = \
            timeseries_df[nominator] / timeseries_df[denominator]

        if not silent:
            display(timeseries_df)

            self._draw_metrics_chart_by_timeline(
                timeseries_df,
                METRIC_COL_NAME,
                description
            )

            periods_df = self._get_testing_df_by_periods(
                timeseries_df,
                grouping_cols=[self.abgroup_col],
                agg_cols=[nominator, denominator],
                agg_funcs={nominator: 'sum', denominator: 'sum'},
                hypothesis=h
            )

            self._draw_metrics_chart_by_timeline_and_fill_between(
                periods_df,
                H_PVALUE_KEY,
                title=description,
                acceptance_band=1-significance_level
            )

        hypothesis_df = timeseries_df\
            .groupby(self.abgroup_col, as_index=False)\
            .sum()

        h.test(
            hypothesis_df,
            save_testing=True
        )

    def _get_testing_df_by_periods(
        self,
        ab_df,
        grouping_cols,
        agg_cols,
        agg_funcs,
        hypothesis
    ):
        periods_of_ab_testing = []
        for period_finish in self.timeseries_period_dates:
            period_ab_df = ab_df\
                [
                    (ab_df[self.timeseries_col].dt.date >= \
                        self.timeseries_period_start_date)
                    & (ab_df[self.timeseries_col].dt.date <= period_finish)
                ]\
                .groupby(
                    grouping_cols,
                    as_index=False
                )[agg_cols].agg(agg_funcs)

            # display(period_finish, period_ab_df)

            test_results = hypothesis.test(
                period_ab_df,
                save_testing=False
            )

            for test_result in test_results.keys():
                periods_of_ab_testing.append([
                    period_finish,
                    test_result,
                    test_results[test_result][H_PVALUE_KEY]
                ])

        return pd.DataFrame(
            periods_of_ab_testing,
            columns=[
                self.timeseries_col,
                self.abgroup_col,
                H_PVALUE_KEY
            ]
        )

    def _draw_metrics_chart_by_timeline(self, df, line_col, title, show=True):
        ax = sns.lineplot(
            data=df,
            hue=self.abgroup_col,
            x=self.timeseries_col,
            y=line_col,
            estimator=None,
            legend='full'
        )
        ax.set_title(title)
        ax.tick_params(axis='x', labelrotation=45)

        if show:
            plt.show()

        return ax

    def _draw_metrics_chart_by_timeline_and_fill_between(
        self,
        df,
        line_col,
        title,
        **kwargs
    ):
        ax = self._draw_metrics_chart_by_timeline(
            df,
            line_col,
            title,
            show=False
        )

        if 'significance_band' in kwargs:
            ax.fill_between(
                df[self.timeseries_col].unique(),
                0,
                kwargs['acceptance_band'],
                color='green',
                alpha=0.2
            )

        plt.show()

    def print_statistical_report(self, correction_method='holm'):
        self.print_metrics_report()
        self.print_multiple_testing_report(correction_method)

    def print_metrics_report(self):
        all_hypothesis_data = []
        for h in self._hypothesis.values():
            h_data = [
                h.get_name()
            ]
            significances = []
            control_metric_set = False

            for _, ch in h.get_combined_hypothesis().items():
                if not ch or np.isnan(ch[H_TEST_GROUP_KEY]):
                    h_data.append(np.NaN)
                    significances.append(np.NaN)
                    continue

                if not control_metric_set:
                    h_data.append(round(ch[H_CONTROL_GROUP_KEY], 3))
                    control_metric_set = True

                uplift = \
                    ch[H_TEST_GROUP_KEY] / ch[H_CONTROL_GROUP_KEY] * 100 - 100
                sign = '+' if uplift >= 0 else ''

                group_comb_res = str(round(ch[H_TEST_GROUP_KEY], 3))\
                    + ' ({sign}{uplift:.2f}%)'.format(sign=sign, uplift=uplift)
                h_data.append(group_comb_res)

                significances.append(
                    '+ (H0 rejected)'
                        if ch[H_SIGNIFICANCE_KEY]
                        else '- (H0 accepted)'
                )

            all_hypothesis_data.append(h_data + significances)

        columns = ['metrics', self.control_group_name]
        sign_columns = []

        for group in self.available_groups:
            if group == self.control_group_name:
                continue

            columns.append(group)
            sign_col_name = 'group {control_group}-{group} sign.'.format(
                control_group=self.control_group_name,
                group=group
            )
            sign_columns.append(sign_col_name)

        display(
            pd.DataFrame(
                all_hypothesis_data,
                columns=columns+sign_columns
            ).set_index('metrics')
        )

    def print_multiple_testing_report(self, method='holm'):
        h_i = 0
        h_dict = {}
        pvalues_list = []
        for h in self._hypothesis.values():
            for ch_name, ch in h.get_combined_hypothesis().items():
                if not ch or np.isnan(ch[H_TEST_GROUP_KEY]):
                    continue

                pvalues_list.append(ch[H_PVALUE_KEY])

                h_dict[h_i] = {
                    'metric': h.get_name(),
                    'combination': ch_name
                }

                h_i += 1

        _, corrected_pvalues_list, _, _ = \
            multipletests(pvalues_list, method=method)

        h_df = pd.DataFrame()
        corr_h_df = pd.DataFrame()

        for i, h_params in h_dict.items():
            pval_col = 'pval. ' + h_params['combination']
            corr_pval_col = 'corrected pval. ' + h_params['combination']

            h_df.loc[h_params['metric'], pval_col] = round(pvalues_list[i], 3)
            corr_h_df.loc[h_params['metric'], corr_pval_col] = \
                round(corrected_pvalues_list[i], 3)

        display(
            method.capitalize() + ' miltiple testing correction is applied',
            h_df.join(corr_h_df)
        )

    def __repr__(self):
        return self.name