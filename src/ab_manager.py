import pandas as pd
import numpy as np

from statsmodels.stats.multitest import multipletests

from IPython.display import display
from IPython.core.display import Markdown

from ab_hypothesis import ABHypothesis
from ab_consts import METRIC_COL_NAME
from ab_consts import DEFAULT_GROUP_NAMES
from ab_consts import H_CONTROL_GROUP_KEY
from ab_consts import H_PVALUE_KEY
from ab_consts import H_SIGNIFICANCE_KEY
from ab_consts import H_TEST_GROUP_KEY
from ab_consts import DEFAULT_SIGNIFICANCE_LEVEL
from ab_consts import H_KIND_CONTINUOUS
from ab_consts import PROPORTION_FORMAT
from ab_consts import UPLIFT_FORMAT
from ab_hypothesis_manager import ABHypothesisManager
from aggregation import Aggregation
from ab_report import ABReport
from charts.pvalue_chart import PValueChart
from charts.period_chart import PeriodChart
from metrics import Metrics


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
        significance_level=None,
        aggregations=None
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

        self.ab_grouping_cols = [
            abgroup_col,
            uniq_id_col
        ]

        ab_df.sort_values(timeseries_col, inplace=True)

        self.aggregations = Aggregation.generate_aggregation(
            ab_df,
            aggregations
        )

        self.ab_hm = ABHypothesisManager(
            significance_level=significance_level
        )

        self.report = ABReport(
            self.aggregations,
            self.ab_hm
        )

        self._combined_groups = self._pair_groups(ab_df)

    def _pair_groups(self, h_df):
        combined_groups = {}
        for group in np.sort(h_df[self.abgroup_col].unique()):
            if not group or group == self.control_group_name:
                continue

            combination_name = str(group) + '-' + str(self.control_group_name)
            combined_groups[combination_name] = {
                'control': self.control_group_name,
                'test': group
            }

        return combined_groups

    def validate_ab_test_data(self, validators = _ALL_VALIDATORS):
        for aggregation in self.aggregations:
            display(Markdown('# Aggregation ' + aggregation.get_name()))
            vl_df = aggregation.get_dataframe()
            display(self._describe_by_group(vl_df))

            if VALIDATION_TYPE__GROUPS_PER_UNIQ_ID in validators:
                display(self._get_groups_stats(vl_df))

    def _get_groups_stats(self, df_w_test_groups):
        return df_w_test_groups\
            .groupby(self.uniq_id_col, as_index=False)[self.abgroup_col]\
            .nunique()\
            .groupby(self.abgroup_col, as_index=False)[self.uniq_id_col]\
            .nunique()

    def _describe_by_group(self, df_to_desc):
        return df_to_desc.groupby(self.abgroup_col).describe().T

    def get_aggregations(self, values=None):
        if values is not None:
            agg_list = []
            for agg_name, agg_values in values.items():
                for agg_value in agg_values:
                    for agg in self.aggregations:
                        if agg.get_name() == agg_name\
                            and agg.get_value() == agg_value:

                            agg_list.append(agg)
                            break

            return agg_list

        return self.aggregations

    def _get_metrics_report(self, metrics_df, h_df):
        rep_df = metrics_df.copy()

        pvalue_cols = list(map(
            lambda c: c + ' pvalue',
            h_df.columns
        ))

        if h_df.shape[0] > 0:
            pvalue_df = h_df[h_df.index == H_PVALUE_KEY]
            pvalue_df.index = metrics_df.index

            rep_df[pvalue_cols] = pvalue_df
        else:
            rep_df[pvalue_cols] = \
                pd.DataFrame([np.NaN] * rep_df.shape[0], index=rep_df.index)

        return rep_df

    def calc_metrics(
        self,
        name,
        mask=None,
        silent=False,
        continuous_measure_col=None,
        nominator_col=None,
        denominator_col=None,
        is_uniq_id_proportions=False,
        na_is_zero=False,
        hypothesis=None,
        aggregation_values=None
    ):
        print('calc_metrics', name)
        for agg in self.get_aggregations(aggregation_values):
            display(agg.get_formatted_name())

            metrics = Metrics(
                name,
                agg.get_dataframe(),
                continuous_measure_col=continuous_measure_col,
                continuous_measure_id_col=self.uniq_id_col,
                nominator_col=nominator_col,
                denominator_col=denominator_col,
                is_uniq_id_proportions=is_uniq_id_proportions,
                na_is_zero=na_is_zero
            )

            agg.add_metrics(metrics)

            if mask is not None:
                metrics.append_mask(mask)

            metrics.append_grouping(
                [
                    self.abgroup_col
                ]
            )

            metrics.calc()

            h = None
            if hypothesis is not None:
                h = ABHypothesis(
                    name=name,
                    nominator_col=nominator_col,
                    denominator_col=denominator_col,
                    continuous_measure_col=continuous_measure_col,
                    control_group_name=self.control_group_name,
                    combined_groups=self._combined_groups,
                    group_col=self.abgroup_col,
                    **hypothesis
                )

                output_df = metrics.get_output()

                output_df.index = \
                    output_df.index.get_level_values(self.abgroup_col)

                h.test(output_df)

                self.ab_hm.add_hypothesis(agg, metrics, h)

            if not silent:
                display(Markdown('### Metrics ' + metrics.get_name()))
                display(self._get_metrics_report(
                    metrics.get_calc(
                        relation_value=self.control_group_name,
                        use_format=True
                    ).T,
                    h.get_test().T
                ))

                PeriodChart(
                    metrics.copy(),
                    hue_col=self.abgroup_col,
                    timeseries_col=self.timeseries_col
                ).draw()

                if h is not None:
                    PValueChart(
                        metrics.copy(),
                        self.abgroup_col,
                        timeseries_col=self.timeseries_col,
                        hypothesis=h
                    ).draw()

    def print_statistics_report(self, correction_method='holm'):
        self.ab_hm.set_multihypothesis_method(correction_method)
        self.report.display()

    def _print_metrics_report(self):
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