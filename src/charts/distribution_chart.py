import itertools
from turtle import title

import numpy as np
from numpy.core.fromnumeric import squeeze
import pandas as pd

import seaborn as sns
import matplotlib.pyplot as plt

from IPython.display import display
from IPython.core.display import Markdown

from .base_chart import BaseChart
from burnaby.ab_consts import OUTLIERS_GROUPS_TYPE
from burnaby.ab_consts import OUTLIERS_METRICS_DATA_TYPE


class DistributionChart(BaseChart):
    def __init__(
        self,
        metrics,
        hue_col=None,
        outliers=None,
        outliers_quantile=None,
        outliers_quantile_min_value=None
    ):
        super().__init__(metrics, hue_col)

        self.outliers = outliers
        self.outliers_quantile = outliers_quantile
        self.outliers_quantile_min_value = outliers_quantile_min_value

    def display_name(self):
        display(Markdown('### Distribution chart ' + self.metrics.get_name()))

    def add_ax_vline(
        self,
        ax,
        df,
        additional_lines,
        hue_col,
        hue_nm,
        x_col,
        y_col,
        color
    ):
        hline_value = additional_lines[
            additional_lines[hue_col] == hue_nm
        ][y_col].values[0]

        x_low_part_df = df[df[y_col] <= hline_value]

        x_value = df[
            df[y_col] == x_low_part_df[y_col].max()
        ][x_col].values[0]

        ax.axvline(x_value, color=color)

    def draw_chart(
        self,
        data_df,
        additional_lines,
        x_col,
        y_col,
        hue_col,
        title=None
    ):
        hl_palette_iter = itertools.cycle(
            sns.color_palette('bright')
        )

        hue_list = np.sort(data_df[hue_col].unique())

        if self.outliers == OUTLIERS_GROUPS_TYPE:
            uniq_hues = data_df[hue_col].nunique()
            lines_n = int(np.ceil(uniq_hues / 2))
            _, axes = plt.subplots(lines_n, 2, squeeze=False, figsize=(16,10))
            faxes = axes.flatten()

            palette_iter = itertools.cycle(sns.color_palette('rocket'))

            for ax, hue_nm in itertools.zip_longest(
                faxes,
                hue_list
            ):
                if hue_nm is None:
                    ax.remove()
                    continue

                color = next(palette_iter)
                h_df = data_df[data_df[hue_col] == hue_nm]
                ax_title = '{title} ({hue_name} = {hue})'.format(
                    title=title,
                    hue_name=hue_col,
                    hue=hue_nm
                )

                sns.barplot(
                    data=h_df,
                    x=x_col,
                    y=y_col,
                    color=color,
                    order=h_df[x_col],
                    ax=ax
                )

                ax.set_title(ax_title)

                if additional_lines is not None:
                    self.add_ax_vline(
                        ax,
                        h_df,
                        additional_lines,
                        hue_col,
                        hue_nm,
                        x_col,
                        y_col,
                        next(hl_palette_iter)
                    )
        else:
            ax = sns.barplot(
                data=data_df,
                x=x_col,
                y=y_col,
                palette=sns.color_palette('rocket'),
                hue=hue_col,
                order=data_df[x_col]
            )

            if additional_lines is not None:
                for hue_nm in hue_list:
                    self.add_ax_vline(
                        ax,
                        data_df,
                        additional_lines,
                        hue_col,
                        hue_nm,
                        x_col,
                        y_col,
                        next(hl_palette_iter)
                    )

            ax.set_title(title)

        plt.show()

    def prepare(self):
        self.metrics.calc(remove_outliers=False)

        output_df = self.metrics.get_output()

        if self.outliers is not None:
            v_mask = output_df[self.metrics.get_output_col()] > \
                self.outliers_quantile_min_value

            v_df = output_df[v_mask]

            quantiles_df = self.metrics.get_quantile_df(
                v_df,
                outliers=self.outliers
            )

            quantiles_df.columns = [self.metrics.get_output_col()]
            quantiles_df = quantiles_df.reset_index()
        else:
            quantiles_df = None
            v_df = output_df

        v_df = v_df \
            .sort_values(by=self.metrics.get_output_col()) \
            .reset_index()

        v_df['x'] = range(0, len(v_df))

        return {
            'data_df': v_df,
            'additional_lines': quantiles_df,
            'x_col': 'x',
            'y_col': self.metrics.get_output_col(),
            'hue_col': self.hue_col,
            'title': self.metrics.get_name()
        }
