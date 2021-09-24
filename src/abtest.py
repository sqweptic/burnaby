from IPython.display import display

class _ABTest:
    def __init__(self, name, dataframe, groups_col) -> None:
        self.name = name
        self.dataframe = dataframe
        self.groups_col = groups_col

    def print_test_res(self):
        print('something something')

    def _display_describe_averages(self):
        display(self.dataframe.groupby(self.groups_col).describe())