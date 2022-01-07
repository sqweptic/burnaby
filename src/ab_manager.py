import pandas as pd
import numpy as np
import seaborn as sns

from IPython.display import display


VALIDATION_TYPE__GROUPS_PER_UNIQ_ID = 'groups_per_uniq_id'
_ALL_VALIDATORS = [
    VALIDATION_TYPE__GROUPS_PER_UNIQ_ID
]

class ABManager:
    def __init__(
        self,
        ab_test_name,
        ab_df,
        group_col,
        timeseries_col,
        uniq_id_col,
        control_group_name = '',
        data_cols = None
    ):
        self.name = ab_test_name
        self.group_col = group_col
        self.timeseries_col = timeseries_col
        self.uniq_id_col = uniq_id_col

        self.uniq_id_grouping_cols = [group_col, timeseries_col, uniq_id_col]
        self.timeseries_grouping_cols = [group_col, timeseries_col]

        if data_cols is None:
            data_cols = np.setdiff1d(
                ab_df.columns,
                self.uniq_id_grouping_cols
            )

        self.ab_df = ab_df.groupby(self.uniq_id_grouping_cols, as_index=False)[data_cols].sum()

    def validate_ab_test_data(self, validators = _ALL_VALIDATORS):
        display(self._describe_by_group(self.ab_df))

        if VALIDATION_TYPE__GROUPS_PER_UNIQ_ID in validators:
            display(self._get_groups_stats(self.ab_df))

    def _get_groups_stats(self, df_w_test_groups):
        return df_w_test_groups\
            .groupby(self.uniq_id_col, as_index=False)[self.group_col]\
            .nunique()\
            .groupby(self.group_col, as_index=False)[self.uniq_id_col]\
            .nunique()

    def _describe_by_group(self, df_to_desc):
        return df_to_desc.groupby(self.group_col).describe().T

    def test_hypothesis_continuous(
        self,
        value_col,
        stat_test,
        description
    ):
        df = self.ab_df\
            .groupby(self.uniq_id_grouping_cols, as_index=False)[value_col]\
            .sum()\
            .groupby(self.timeseries_grouping_cols, as_index=False)\
            .agg(metric = (value_col, 'mean'))

        display(df)

        self._draw_metrics_chart_by_timeline(df, 'metric', description)

    def test_hypothesis_rational(
        self,
        nominator,
        denominator,
        stat_test,
        description,
        uniq_id_rel
    ):
        if uniq_id_rel:
            df = self.ab_df.groupby(self.timeseries_grouping_cols, as_index=False)[[nominator, denominator]].agg({
                nominator: lambda x: 1 if (x > 0).any() else 0,
                denominator: lambda x: 1 if (x > 0).any() else 0
            })
        else:
            df = self.ab_df.groupby(self.timeseries_grouping_cols, as_index=False)[[nominator, denominator]].sum()

        df['metric'] = df[nominator] / df[denominator]

        display(df)

        self._draw_metrics_chart_by_timeline(df, 'metric', description)

    def _draw_metrics_chart_by_timeline(self, df, feature_col, name):
        mplot = sns.lineplot(
            data=df,
            hue=self.group_col,
            x=self.timeseries_col,
            y=feature_col,
            estimator=None,
            legend='full'
        )
        mplot.set_title(name)

        return mplot

    def _draw_metrics_chart_by_timeline_and_fill_between(self, df, feature_col, name, **kwargs):
        plt = self._draw_metrics_chart_by_timeline(df, feature_col, name)

        if 'fill_between_x' in kwargs:
            plt.fill_between(
                df[self.timeline_col].unique(),
                0,
                kwargs['fill_between_x'],
                color='green',
                alpha=0.2
            )

    def __repr__(self):
        return self.name