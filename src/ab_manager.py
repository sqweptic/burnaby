import pandas as pd
import numpy as np
import seaborn as sns

from IPython.display import display

from ab_hypothesis import Hypothesis
from ab_consts import MERTIC_COL_NAME
from ab_consts import DEFAULT_GROUP_NAMES


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
        control_group_name = None,
        data_cols = None
    ):
        self.name = ab_test_name
        self.group_col = group_col
        self.timeseries_col = timeseries_col
        self.uniq_id_col = uniq_id_col

        if control_group_name is None:
            self.control_group_name = control_group_name
        else:
            try:
                self.control_group_name = np.setdiff1d(ab_df[group_col].unique(), DEFAULT_GROUP_NAMES)[0]
            except IndexError:
                display('control group is not defined')

        self.uniq_id_grouping_cols = [group_col, timeseries_col, uniq_id_col]
        self.timeseries_grouping_cols = [group_col, timeseries_col]

        if data_cols is None:
            data_cols = np.setdiff1d(
                ab_df.columns,
                self.uniq_id_grouping_cols
            )

        self.ab_df = ab_df.groupby(self.uniq_id_grouping_cols, as_index=False)[data_cols].sum()

        self._hypothesis = {}
        self._combined_groups = self._pair_groups(ab_df)

    def _pair_groups(self, h_df):
        combined_groups = {}
        for group in np.sort(h_df[self.group_col].unique()):
            display(group)
            if group == self.control_group_name:
                continue
            display(self.control_group_name, group)
            combined_groups[str(self.control_group_name) + '-' + str(group)] = {
                'control': self.control_group_name,
                'test': group
            }
        display(combined_groups)

        return combined_groups

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
        description,
        na_is_zero=True
    ):
        h_name = Hypothesis.generate_hypothesis_name(description, value_col=value_col)

        if h_name in self._hypothesis:
            h = self._hypothesis[h_name]
        else:
            h = Hypothesis(
                value_col=value_col,
                name=description,
                stat_test=stat_test,
                group_col=self.group_col,
                control_group_name=self.control_group_name,
                combined_groups=self._combined_groups
            )
            self._hypothesis[h_name] = h

        hypothesis_df = self.ab_df

        if na_is_zero:
            hypothesis_df[value_col] = hypothesis_df[value_col].fillna(0)
        else:
            hypothesis_df = hypothesis_df[~hypothesis_df[value_col].isna()]

        hypothesis_df = hypothesis_df.groupby(self.uniq_id_grouping_cols, as_index=False)[value_col]\
            .sum()
        hypothesis_df
        timeseries_df = hypothesis_df\
            .groupby(self.timeseries_grouping_cols, as_index=False)\
            .agg(metric = (value_col, 'mean'))

        display(timeseries_df)

        self._draw_metrics_chart_by_timeline(timeseries_df, MERTIC_COL_NAME, description)

        h.test(hypothesis_df, stat_test)

    def test_hypothesis_relational(
        self,
        nominator,
        denominator,
        stat_test,
        description,
        uniq_id_rel = False
    ):
        h_name = Hypothesis.generate_hypothesis_name(description, nom_col=nominator, den_col=denominator)

        if h_name in self._hypothesis:
            h = self._hypothesis[h_name]
        else:
            h = Hypothesis(
                nom_col=nominator,
                den_col=denominator,
                name=description,
                stat_test=stat_test,
                group_col=self.group_col,
                control_group_name=self.control_group_name,
                combined_groups=self._combined_groups
            )
            self._hypothesis[h_name] = h

        if uniq_id_rel:
            timeseries_df = self.ab_df.groupby(self.timeseries_grouping_cols, as_index=False)[[nominator, denominator]].agg({
                nominator: lambda x: 1 if (x > 0).any() else 0,
                denominator: lambda x: 1 if (x > 0).any() else 0
            })
        else:
            timeseries_df = self.ab_df.groupby(self.timeseries_grouping_cols, as_index=False)[[nominator, denominator]].agg({
                nominator: lambda x: x[x > 0].shape[0] if (x > 0).any() else 0,
                denominator: lambda x: x[x > 0].shape[0] if (x > 0).any() else 0
            })

        timeseries_df[MERTIC_COL_NAME] = timeseries_df[nominator] / timeseries_df[denominator]

        display(timeseries_df)

        self._draw_metrics_chart_by_timeline(timeseries_df, MERTIC_COL_NAME, description)

        hypothesis_df = timeseries_df.groupby(self.group_col, as_index=False).sum()

        h.test(hypothesis_df, stat_test)

    def _draw_metrics_chart_by_timeline(self, df, feature_col, name):
        plt = sns.lineplot(
            data=df,
            hue=self.group_col,
            x=self.timeseries_col,
            y=feature_col,
            estimator=None,
            legend='full'
        )
        plt.set_title(name)

        return plt

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