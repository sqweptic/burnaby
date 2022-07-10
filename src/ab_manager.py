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
                'control group name is undefined or is not in dataframe'
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

        self.info_df = pd.DataFrame(
            [
                ['AB test name: ' + self.name],
                [
                    'Period: ' +
                    str(ab_df[timeseries_col].min()) +
                    ' - ' +
                    str(ab_df[timeseries_col].max())
                ],
                ['Number of groups: ' + str(ab_df[abgroup_col].nunique())],
                ['Unique ids: ' + str(ab_df[uniq_id_col].nunique())],
                ['Significance level: ' + str(significance_level)],
            ],
            columns=['']
        )

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
        outliers=None,
        outliers_quantile=None,
        outliers_quantile_min_value=None,
        is_uniq_id_proportions=False,
        na_is_zero=False,
        hypothesis=None,
        aggregation_values=None
    ):
        for agg in self.get_aggregations(aggregation_values):
            display(agg.get_formatted_name())

            metrics = Metrics(
                name,
                agg.get_dataframe(),
                continuous_measure_col=continuous_measure_col,
                continuous_measure_id_col=self.uniq_id_col,
                outliers=outliers,
                outliers_quantile=outliers_quantile,
                outliers_quantile_min_value=outliers_quantile_min_value,
                relation_value=self.control_group_name,
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

            self.report.clear_report()

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
                        calc_relation=True,
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
        self.ab_hm.set_multiple_hypothesis_correction(correction_method)

        self.report.display()

    def save_report_to_excel(self, filename_or_path, correction_method='holm'):
        self.ab_hm.set_multiple_hypothesis_correction(correction_method)

        self.report.save_to_excel(
            filename_or_path,
            info_df=self.info_df
        )

        print('saved to file', filename_or_path)

    def __repr__(self):
        return self.name