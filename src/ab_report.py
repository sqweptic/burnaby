import pandas as pd

from IPython.display import display
from IPython.core.display import Markdown

from .ab_consts import R_AGGREGATION_COL
from .ab_consts import METRIC_COL_NAME


REPORTS_BOTTOM_MARGIN = 3

class ABReport:
    def __init__(self, aggregations, ab_hypothesis_manager):
        self.aggregations = aggregations
        self.ab_hm = ab_hypothesis_manager

        self.clear_report()

    def clear_report(self):
        self.report_df = None
        self.report_mh_df = None

    def prepare_report(self):
        if self.report_df is not None:
            return self.report_df

        self.report_df = pd.DataFrame()

        for agg in self.aggregations:
            agg_df = pd.DataFrame()
            print('agg: ', agg.get_full_name())
            for metrics in agg.get_metrics_list():
                m_df = metrics.get_calc(
                    calc_relation=True,
                    use_format=True
                )

                hcorr_pvalues_df = self.ab_hm.get_hypothesis_corrected_pvalue(
                    agg,
                    metrics
                )

                hcorr_pvalues_df.index = list(
                    map(
                        lambda i: hcorr_pvalues_df.columns[0] + ' ' + str(i),
                        hcorr_pvalues_df.index
                    )
                )
                hcorr_pvalues_df.columns = m_df.columns
                m_df = m_df.append(hcorr_pvalues_df)

                hacceptance_df = self.ab_hm.get_hypothesis_acceptance(
                    agg,
                    metrics
                )

                hacceptance_df.index = list(
                    map(
                        lambda i: hacceptance_df.columns[0] + ' ' + str(i),
                        hacceptance_df.index
                    )
                )
                hacceptance_df.columns = m_df.columns
                m_df = m_df.append(hacceptance_df)
                m_df.columns = [metrics.get_name()]

                agg_df = agg_df.append(m_df.T)

                agg_df[R_AGGREGATION_COL] = agg.get_full_name()
            self.report_df = self.report_df.append(agg_df)

    def prepare_multiple_hypothesis_report(self):
        if self.report_mh_df is not None:
            return self.report_mh_df

        self.report_mh_df = pd.DataFrame()

        for agg in self.aggregations:
            agg_df = pd.DataFrame()

            for metrics in agg.get_metrics_list():
                h_df = self.ab_hm.get_hypothesis(agg, metrics).get_test()

                hcorr_pvalues_df = self.ab_hm.get_hypothesis_corrected_pvalue(
                    agg,
                    metrics
                )

                hacceptance_df = self.ab_hm.get_hypothesis_acceptance(
                    agg,
                    metrics
                )

                corrected_h_df = h_df.join(
                    hcorr_pvalues_df
                ).join(
                    hacceptance_df
                )

                corrected_h_df.index = pd.MultiIndex.from_product(
                    [[metrics.get_name()], corrected_h_df.index],
                    names=[METRIC_COL_NAME, '']
                )

                agg_df = agg_df.append(corrected_h_df)

                agg_df[R_AGGREGATION_COL] = agg.get_full_name()
            self.report_mh_df = self.report_mh_df.append(agg_df)

    def display(self):
        self.prepare_report()
        self.prepare_multiple_hypothesis_report()

        for agg in self.aggregations:
            agg_df = self.report_df[
                self.report_df[R_AGGREGATION_COL] == agg.get_full_name()
            ]

            agg_mh_df = self.report_mh_df[
                self.report_mh_df[R_AGGREGATION_COL] == agg.get_full_name()
            ]

            display(agg.get_formatted_name())

            display(agg_df.drop(columns=[R_AGGREGATION_COL]))

            display(agg_mh_df.drop(columns=[R_AGGREGATION_COL]))

    def save_to_excel(self, filename_or_path, info_df = None):
        self.prepare_multiple_hypothesis_report()
        self.prepare_report()

        with pd.ExcelWriter(
                filename_or_path
            ) as fexcel:
            for agg in self.aggregations:
                if agg.get_value() == '*':
                    sheet_name = '_all'
                else:
                    sheet_name = agg.get_value()

                start_row = 0

                agg_df = self.report_df[
                    self.report_df[R_AGGREGATION_COL] == agg.get_full_name()
                ]

                agg_mh_df = self.report_mh_df[
                    self.report_mh_df[R_AGGREGATION_COL] == agg.get_full_name()
                ]


                if info_df is not None:
                    info_df.to_excel(
                        fexcel,
                        sheet_name=sheet_name,
                        startrow=start_row,
                        index=None
                    )

                    start_row += info_df.shape[0] + 1 + REPORTS_BOTTOM_MARGIN

                agg_df.drop(columns=[R_AGGREGATION_COL]).to_excel(
                    fexcel,
                    sheet_name=sheet_name,
                    startrow=start_row
                )

                start_row += agg_df.shape[0] + 1 + REPORTS_BOTTOM_MARGIN

                agg_mh_df.drop(columns=[R_AGGREGATION_COL]).to_excel(
                    fexcel,
                    sheet_name=sheet_name,
                    startrow=start_row
                )
