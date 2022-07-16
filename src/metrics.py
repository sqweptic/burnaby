from copy import copy

import numpy as np
import pandas as pd

from .ab_consts import METRIC_COL_NAME
from .ab_consts import UPLIFT_FORMAT
from .ab_consts import PROPORTION_FORMAT
from .ab_consts import CONTINUOUS_MEASURE_FORMAT
from .ab_consts import OUTLIERS_GROUPS_TYPE
from .ab_consts import OUTLIERS_METRICS_DATA_TYPE


QUANTILE_COL_NAME = '_quantile'


def uniq_id_proportion(x):
    return (x > 0).sum()

def no_uniq_id_proportion(x):
    return sum(x)

class Metrics:
    def __init__(
        self,
        name,
        data_df,
        mask=None,
        grouping=None,
        outliers=None,
        outliers_quantile=None,
        outliers_quantile_min_value=None,
        format_str=None,
        relation_format_str=None,
        relation_value=None,
        continuous_measure_col=None,
        continuous_measure_id_col=None,
        nominator_col=None,
        denominator_col=None,
        is_uniq_id_proportions=False,
        na_is_zero=False
    ):
        self.name = name

        if mask is not None:
            self.data_df = data_df[mask]
        else:
            self.data_df = data_df

        self.grouping = copy(grouping)

        self.continuous_measure_col = continuous_measure_col
        self.continuous_measure_id_col = continuous_measure_id_col
        self.relation_value = relation_value

        self.nominator_col = nominator_col
        self.denominator_col = denominator_col
        self.na_is_zero = na_is_zero
        self.is_uniq_id_proportions = is_uniq_id_proportions
        self.outliers=outliers
        self.outliers_quantile=outliers_quantile
        self.outliers_quantile_min_value = outliers_quantile_min_value

        if is_uniq_id_proportions:
            self.proportion_func = uniq_id_proportion
        else:
            self.proportion_func = no_uniq_id_proportion

        if format_str is not None:
            self.format_str = format_str
        elif self.continuous_measure_col is not None:
            self.format_str = CONTINUOUS_MEASURE_FORMAT
        else:
            self.format_str = PROPORTION_FORMAT

        if relation_format_str is not None:
            self.relation_format_str = relation_format_str
        else:
            self.relation_format_str = UPLIFT_FORMAT

    def get_name(self):
        return self.name

    def get_output_col(self):
        if self.continuous_measure_col is not None:
            return self.continuous_measure_col
        return (self.nominator_col, self.denominator_col)

    def get_col(self):
        return METRIC_COL_NAME

    def append_mask(self, mask):
        self.data_df = self.data_df[mask]

    def append_grouping(self, grouping):
        if self.grouping is not None:
            self.grouping += grouping
        else:
            self.grouping = copy(grouping)

    def set_grouping(self, grouping):
        self.grouping = copy(grouping)

    def get_data(self):
        return self.data_df

    def copy(self):
        return Metrics(
            name=self.name,
            data_df=self.data_df,
            grouping=copy(self.grouping),
            format_str=self.format_str,
            outliers=self.outliers,
            outliers_quantile=self.outliers_quantile,
            outliers_quantile_min_value=self.outliers_quantile_min_value,
            relation_format_str=self.relation_format_str,
            relation_value=self.relation_value,
            continuous_measure_col=self.continuous_measure_col,
            continuous_measure_id_col=self.continuous_measure_id_col,
            is_uniq_id_proportions=self.is_uniq_id_proportions,
            nominator_col=self.nominator_col,
            denominator_col=self.denominator_col,
            na_is_zero=self.na_is_zero
        )

    def _get_grouping(self, grouping, add_continuous_measure_id_col):
        _grouping = []
        if grouping is not None:
            _grouping = grouping

        if self.grouping is not None:
            if _grouping is not None:
                _grouping += self.grouping
            else:
                _grouping = self.grouping

        if self.continuous_measure_col is not None \
            and self.continuous_measure_id_col is not None \
            and add_continuous_measure_id_col:
            _grouping += [self.continuous_measure_id_col]

        return _grouping

    def group_data(
        self,
        grouping,
        interm_df,
        add_continuous_measure_id_col=False
    ):
        _grouping = self._get_grouping(
            grouping,
            add_continuous_measure_id_col
        )

        if _grouping is not None:
            interm_df = interm_df\
                .groupby(_grouping)

        return interm_df

    def get_quantile_df(self, m_df, outliers, grouping=None):
        grp = self._get_grouping(grouping, False)

        if outliers == OUTLIERS_GROUPS_TYPE:
            m_grouped_df = m_df.groupby(grp)

            grp_q_df = m_grouped_df.quantile(self.outliers_quantile)
            grp_q_df.columns = [QUANTILE_COL_NAME]

            return grp_q_df
        elif outliers == OUTLIERS_METRICS_DATA_TYPE:
            grp_q_index = m_df.reset_index()[grp].drop_duplicates()

            if len(grp) > 1:
                df_index = pd.MultiIndex.from_arrays(
                    grp_q_index.T.values,
                    names=grp
                )
            else:
                df_index = pd.Index(
                    grp_q_index.T.values[0],
                    name=grp[0]
                )

            return pd.DataFrame(
                [
                    m_df[self.continuous_measure_col] \
                        .quantile(self.outliers_quantile)
                ] * len(grp_q_index),
                columns=[QUANTILE_COL_NAME],
                index=df_index
            )

        else:
            raise Exception('wrong outliers removing type')

    def remove_outliers(self, grouping, m_df):
        if self.outliers is None:
            return m_df

        if self.outliers_quantile_min_value is not None:
            no_min_value_m_df = m_df[
                m_df[self.continuous_measure_col] >
                    self.outliers_quantile_min_value
            ]
        else:
            no_min_value_m_df = m_df

        quantile_df = self.get_quantile_df(
            no_min_value_m_df,
            outliers=self.outliers,
            grouping=grouping
        )

        m_joined_q_df = m_df.join(quantile_df)

        no_outliers_m_df = m_joined_q_df[
            m_joined_q_df[self.continuous_measure_col] <= \
                m_joined_q_df[QUANTILE_COL_NAME]
        ]

        return no_outliers_m_df.drop(columns=quantile_df.columns)

    def calc(
        self,
        mask=None,
        grouping=None,
        remove_outliers=True
    ):
        interm_df = self.data_df

        if mask is not None:
            interm_df = interm_df[mask]

        interm_df = self.group_data(grouping, interm_df, True)

        if self.continuous_measure_col is None:
            output_df = interm_df[[self.nominator_col, self.denominator_col]]\
                .agg({
                    self.nominator_col: self.proportion_func,
                    self.denominator_col: self.proportion_func
                })

            metrics_df = output_df

            metrics_df[METRIC_COL_NAME] = (output_df[self.nominator_col] /\
                output_df[self.denominator_col])

        else:
            output_df = interm_df[[self.continuous_measure_col]].sum()

            if remove_outliers:
                output_df = self.remove_outliers(grouping, output_df)

            metrics_df = output_df

            metrics_df.index = metrics_df.index.droplevel(
                [self.continuous_measure_id_col]
            )

            metrics_df = metrics_df.reset_index()

            metrics_df = self.group_data(grouping, metrics_df, False).sum()

            columns = []
            for col in metrics_df.columns:
                if col == self.continuous_measure_col:
                    columns.append(METRIC_COL_NAME)
                else:
                    columns.append(col)
            metrics_df.columns = columns

        self.metrics_df = metrics_df
        self.output_df = output_df

        return output_df

    def set_output(self, output_df):
        self.output_df = output_df

    def get_output(self):
        return self.output_df

    def get_calc(
        self,
        calc_relation=False,
        use_format=False
    ):
        m_df = self.metrics_df[[METRIC_COL_NAME]]
        foutput_dt = m_df.copy()

        if use_format:
            foutput_dt = foutput_dt.applymap(self.format_str.format)

        if calc_relation:
            if m_df[m_df.index == self.relation_value].shape[0] == 0:
                rel = np.NaN
            else:
                rel = m_df[m_df.index == self.relation_value].values[0][0]

            no_rel_value_df = m_df[m_df.index != self.relation_value]

            rel_columns = list(map(
                lambda v: str(v) + '-' + str(self.relation_value),
                no_rel_value_df.index
            ))

            rel_output_df = (no_rel_value_df / rel) - 1
            rel_output_df.index = rel_columns

            if rel is not np.NaN and use_format:
                    rel_output_df = rel_output_df\
                        .applymap(self.relation_format_str.format)

            foutput_dt = foutput_dt.append(rel_output_df)

        return foutput_dt
