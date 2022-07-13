import imp
import pandas as pd

import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

from IPython.display import display
from IPython.core.display import Markdown

from .base_chart import BaseChart


class PeriodChart(BaseChart):
    def __init__(
        self,
        metrics,
        hue_col=None,
        timeseries_col=None,
        date_unit='day'
    ):
        super().__init__(metrics, hue_col)

        self.timeseries_col = timeseries_col
        self.date_unit = date_unit
        self.tmp_timeseries_col = str(self.__hash__()) + timeseries_col

    def display_name(self):
        display(Markdown('### Period chart ' + self.metrics.get_name()))

    def draw_chart(self, data_df, x_col, y_col, hue_col, title=None, show=True):
        ax = super().draw_chart(data_df, x_col, y_col, hue_col, title, False)

        if show:
            # ax.yaxis.set_major_formatter(PercentFormatter(1))
            plt.show()

        return ax

    def _as_date_type(self, metrics):
        pd.options.mode.chained_assignment = None
        m_df = metrics.get_data()

        if m_df.dtypes[self.timeseries_col] == 'object':
            m_df[self.tmp_timeseries_col] = pd.to_datetime(
                m_df[self.timeseries_col]
            )
        else:
            m_df[self.tmp_timeseries_col] = m_df[self.timeseries_col]

        if self.date_unit == 'day':
            m_df[self.tmp_timeseries_col] = \
                m_df[self.tmp_timeseries_col].dt.to_period('D')

        pd.options.mode.chained_assignment = 'warn'

    def prepare(self):
        self._as_date_type(self.metrics)

        self.metrics.append_grouping([self.tmp_timeseries_col])
        self.metrics.calc()
        r = self.metrics.get_calc(use_format=False).reset_index()

        r[self.timeseries_col] = r[self.tmp_timeseries_col].astype(str)

        return {
            'data_df': r,
            'x_col': self.timeseries_col,
            'y_col': self.metrics.get_col(),
            'hue_col': self.hue_col,
            'title': self.metrics.get_name()
        }

    def clean_after(self):
        m_df = self.metrics.get_data()

        del m_df[self.tmp_timeseries_col]
