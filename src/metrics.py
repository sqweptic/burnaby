from IPython.display import display

# from ab_hypothesis import Hypothesis
from ab_consts import METRIC_COL_NAME


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
        format_str=None,
        relation_format_str=None
    ):
        self.name = name
        self.data_df = data_df
        self.mask = mask
        self.grouping = grouping
        self.format_str=format_str
        self.relation_format_str=relation_format_str

    def append_mask(self, mask):
        if self.mask is None:
            self.mask = mask
        else:
            self.mask &= mask

    def set_grouping(self, grouping):
        self.grouping = grouping

    def calc(
        self,
        continue_measure_col=None,
        nominator_col=None,
        denominator_col=None,
        is_uniq_id_proportions=False,
        na_is_zero=False
    ):
        if is_uniq_id_proportions:
            proportion_func = uniq_id_proportion
        else:
            proportion_func = no_uniq_id_proportion

        interm_df = self.data_df

        if self.mask is not None:
            interm_df = interm_df[self.mask]

        if self.grouping is not None:
            interm_df = interm_df\
                .groupby(self.grouping)

        if continue_measure_col is None:
            self.output_df = interm_df[[nominator_col, denominator_col]]\
                .agg({
                    nominator_col: proportion_func,
                    denominator_col: proportion_func
                })

            self.output_df[METRIC_COL_NAME] = (self.output_df[nominator_col] /\
                self.output_df[denominator_col])

        else:
            self.output_df[METRIC_COL_NAME] = interm_df[[continue_measure_col]]

    def get_output(self):
        return self.output_df

    def get_calc(
        self,
        relation_value=None,
        format_str=None,
        relation_format_str=None,
    ):
        m_df = self.output_df[[METRIC_COL_NAME]]
        foutput_dt = m_df.copy()

        if format_str is not None:
            foutput_dt = foutput_dt.applymap(format_str.format)
        elif self.format_str is not None:
            foutput_dt = foutput_dt.applymap(self.format_str.format)

        if relation_value is not None:
            rel = m_df[m_df.index == relation_value].values[0][0]

            no_rel_value_df = m_df[m_df.index != relation_value]

            rel_columns = list(map(
                lambda v: str(v) + '-' + str(relation_value),
                no_rel_value_df.index
            ))

            rel_output_df = (no_rel_value_df / rel) - 1
            rel_output_df.index = rel_columns

            if relation_format_str is not None:
                rel_output_df = rel_output_df\
                    .applymap(relation_format_str.format)
            elif self.relation_format_str is not None:
                rel_output_df = rel_output_df\
                    .applymap(self.relation_format_str.format)

            foutput_dt = foutput_dt.append(rel_output_df).T
        else:
            foutput_dt = foutput_dt.T

        return foutput_dt
