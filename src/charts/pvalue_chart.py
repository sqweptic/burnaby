import pandas as pd

import seaborn as sns
import matplotlib.pyplot as plt

from IPython.display import display
from IPython.core.display import Markdown

from .period_chart import PeriodChart
from .base_chart import BaseChart
from burnaby.ab_consts import H_PVALUE_KEY


class PValueChart(PeriodChart):
    def __init__(
        self,
        metrics,
        hue_col,
        timeseries_col,
        hypothesis
    ):
        super().__init__(metrics, hue_col, timeseries_col)

        self.h = hypothesis

    def display_name(self):
        display(Markdown('### Pvalue By timeseries ' + self.metrics.get_name()))

    def get_periods(self, m_df):
        start_dt = m_df[self.timeseries_col].min()
        uniq_dts = sorted(m_df[self.timeseries_col].unique())

        for dt in uniq_dts:
            yield start_dt, dt

    def prepare(self):
        self._as_date_type(self.metrics)
        m_df = self.metrics.get_data()

        r = None
        for period_start, period_end in self.get_periods(m_df):
            self.metrics.calc()

            self.metrics.calc(
                mask=(m_df[self.timeseries_col] >= period_start)
                    & (m_df[self.timeseries_col] <= period_end)
            )

            output_df = self.metrics.get_output()

            pv_df = self.h.test(output_df, save_testing=False)[[H_PVALUE_KEY]]

            pv_df[self.timeseries_col] = period_end

            if r is None:
                r = pv_df
            else:
                r = r.append(pv_df)

        r.index.name = self.hue_col
        r.reset_index(inplace=True)

        return {
            'data_df': r,
            'x_col': self.timeseries_col,
            'y_col': H_PVALUE_KEY,
            'hue_col': self.hue_col,
            'title': self.metrics.get_name()
        }

    def draw_chart(
        self,
        data_df,
        x_col,
        y_col,
        hue_col,
        title=None,
        **kwargs
    ):
        ax = super().draw_chart(
            data_df,
            x_col,
            y_col,
            hue_col,
            title,
            show=False
        )

        ax.fill_between(
            data_df[x_col].unique(),
            0,
            self.h.get_significance_level(),
            color='green',
            alpha=0.2
        )

        plt.ylim([0, 1])
        plt.show()
