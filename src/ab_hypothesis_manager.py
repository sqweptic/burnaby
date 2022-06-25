from ab_consts import DEFAULT_SIGNIFICANCE_LEVEL


class ABHypothesisManager:
    def __init__(
        self,
        aggregations,
        significance_level = DEFAULT_SIGNIFICANCE_LEVEL
    ):
        self._hypothesis = {}
        self.aggregations = aggregations
        self.significance_level = significance_level

    def add_hypothesis(self, agg, metrics):
        self._hypothesis[(agg, metrics)]
