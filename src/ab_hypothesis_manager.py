from collections import OrderedDict

import numpy as np

from IPython.display import display

from statsmodels.stats.multitest import multipletests

from .ab_consts import DEFAULT_SIGNIFICANCE_LEVEL
from .ab_consts import H_PVALUE_KEY
from .ab_consts import METRIC_COL_NAME
from .ab_consts import H_SIGNIFICANCE_KEY
from .ab_consts import H_SIGNIFICANCE_LEVEL_KEY


_CORRECTION_PREFIX = 'corrected_'

class ABHypothesisManager:
    def __init__(
        self,
        significance_level = DEFAULT_SIGNIFICANCE_LEVEL,
        correction_method = None
    ):
        self._hypothesis = OrderedDict()
        self.significance_level = significance_level
        self.mh_correction_method = correction_method

        self.with_correction_by_agg_dataframes = {}

    def add_hypothesis(self, agg, metrics, h):
        self._hypothesis[(agg.get_full_name(), metrics.get_name())] = h

        if agg in self.with_correction_by_agg_dataframes:
            del self.with_correction_by_agg_dataframes[agg]

    def get_hypothesis(self, agg, metrics):
        return self._hypothesis[(agg.get_full_name(), metrics.get_name())]

    def set_multiple_hypothesis_correction(self, correction_method):
        self.mh_correction_method = correction_method

    def get_correction(self, agg):
        with_correction_df = None

        # if agg in self.with_correction_by_agg_dataframes:
        #     return self.with_correction_by_agg_dataframes[agg]

        for hagg, hmetrics in self._hypothesis.keys():
            if agg.get_full_name() == hagg:
                h = self._hypothesis[(hagg, hmetrics)]\
                    .get_test().reset_index()

                h[METRIC_COL_NAME] = hmetrics

                if with_correction_df is None:
                    with_correction_df = h
                else:
                    with_correction_df = with_correction_df.append(h)

        _, corrected_pvalues_list, _, _ = multipletests(
            with_correction_df[H_PVALUE_KEY],
            method=self.mh_correction_method
        )

        with_correction_df[_CORRECTION_PREFIX + H_PVALUE_KEY] = \
            corrected_pvalues_list

        with_correction_df[_CORRECTION_PREFIX + H_SIGNIFICANCE_KEY] = \
            list(map(
                lambda pvalue, slevel:
                    np.NaN if np.isnan(pvalue) else slevel > pvalue,
                corrected_pvalues_list,
                with_correction_df[H_SIGNIFICANCE_LEVEL_KEY]
            ))

        self.with_correction_by_agg_dataframes[agg] = with_correction_df

        return with_correction_df

    def get_metrics_correction_result(self, corrected_df, agg, metrics):
        metrics_corrected_df = corrected_df[
            corrected_df[METRIC_COL_NAME] == metrics.get_name()
        ]

        metrics_corrected_df = metrics_corrected_df.set_index(
            self.get_hypothesis(agg, metrics).get_test().index
        )

        return metrics_corrected_df

    def get_hypothesis_corrected_pvalue(self, agg, metrics):
        whole_corrected_df = self.get_correction(agg)

        metrics_corrected_df = self.get_metrics_correction_result(
            whole_corrected_df,
            agg,
            metrics
        )

        return metrics_corrected_df[[_CORRECTION_PREFIX + H_PVALUE_KEY]]

    def get_hypothesis_acceptance(self, agg, metrics):
        whole_corrected_df = self.get_correction(agg)

        metrics_corrected_df = self.get_metrics_correction_result(
            whole_corrected_df,
            agg,
            metrics
        )

        return metrics_corrected_df[[_CORRECTION_PREFIX + H_SIGNIFICANCE_KEY]]
