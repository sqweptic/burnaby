import seaborn as sns
import matplotlib.pyplot as plt


class BaseChart:
    def __init__(
        self,
        metrics,
        hue_col
    ):
        self.metrics = metrics
        self.hue_col = hue_col

    def prepare(self):
        pass

    def draw_chart(self, data_df, x_col, y_col, hue_col, title=None, show=True):
        ax = sns.lineplot(
            data=data_df,
            hue=hue_col,
            x=x_col,
            y=y_col,
            estimator=None,
            legend='full'
        )

        if title is not None:
            ax.set_title(title)

        ax.tick_params(axis='x', labelrotation=45)

        if show:
            plt.show()

        return ax

    def display_name(self):
        pass

    def draw(self):
        self.display_name()
        data = self.prepare()
        self.draw_chart(**data)
