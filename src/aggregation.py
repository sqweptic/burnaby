from IPython.core.display import Markdown, display
import numpy as np

from metrics import Metrics

_USE_WHOLE_DATA_KEYWORDS = [
    '*',
    None,
    ''
]


class Aggregation:
    def __init__(
        self,
        agg_name,
        agg_value,
        data_df,
        grouping_cols = None
    ) -> None:
        self.agg_name = agg_name
        self.is_whole_data = agg_name in _USE_WHOLE_DATA_KEYWORDS

        self.agg_value = _USE_WHOLE_DATA_KEYWORDS[0] if self.is_whole_data\
            else agg_value

        self.data_df = data_df
        self.grouping_cols = grouping_cols

        self.metrics = []

    def get_name(self):
        return self.agg_name

    def get_value(self):
        return self.agg_value

    def __repr__(self) -> str:
        return self.get_full_name()

    def get_full_name(self):
        if self.is_whole_data:
            return 'Whole dataset'

        return self.agg_name + (
            ' = ' + self.agg_value if self.agg_value is not None else ''
        )

    def get_name_list(self, return_specified):
        if return_specified:
            return self.spec_agg

        return [self.whole_data_col] + self.spec_agg


    def add_metrics(self, metrics):
        self.metrics.append(metrics)

    # def create_metrics(self, name):
    #     metrics = Metrics(
    #         name,
    #         data_df=self.get_dataframe()
    #     )
    #     self.add_metrics(metrics)

    #     return metrics

    def get_mask(self):
        if not self.is_whole_data:
            return self.data_df[self.agg_name] == self.agg_value

    def get_dataframe(self):
        mask = self.get_mask()
        if mask is not None:
            return self.data_df[mask]

        return self.data_df

    def get_group_col_list(self):
        if self.is_whole_data:
            return []
        return [self.agg_name]

    def get_formatted_name(self):
        return Markdown('# Aggregation: ' + self.get_full_name())

    @staticmethod
    def generate_aggregation(data_df, aggregations):
        aggs = []
        if aggregations is None:
            aggs.append(Aggregation(
                _USE_WHOLE_DATA_KEYWORDS[0],
                None,
                data_df
            ))
        else:
            print('here')
            for agg_col in aggregations:
                if agg_col in _USE_WHOLE_DATA_KEYWORDS:
                    aggs.append(Aggregation(
                        _USE_WHOLE_DATA_KEYWORDS[0],
                        None,
                        data_df
                    ))
                    continue

                agg_values = data_df[agg_col].drop_duplicates()
                for agg_value in agg_values:
                    display(agg_col, agg_value)
                    aggs.append(Aggregation(
                        agg_col,
                        agg_value,
                        data_df
                    ))

        return aggs