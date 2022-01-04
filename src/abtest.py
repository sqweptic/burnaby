from IPython.display import display

class _ABTest:
    def __init__(
        self,
        ab_test_name,
        ab_df,
        group_col,
        date_col,
        uniq_id_col,
        control_group_name,
        aggregate_cols,
        data_cols
    ):
        self.name = ab_test_name
        self.ab_df = ab_df
        self.group_col = group_col

    def print_test_res(self):
        print('something something')

    def _describe_by_group(self, df_to_desc):
        return df_to_desc.groupby(self.group_col).describe().T

    def _display_describe(self):
        display(self._describe_by_group(self.ab_df))
