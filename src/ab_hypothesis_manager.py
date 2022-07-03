from ab_consts import DEFAULT_SIGNIFICANCE_LEVEL


class ABHypothesisManager:
    def __init__(
        self,
        significance_level = DEFAULT_SIGNIFICANCE_LEVEL,
        correction_method = None
    ):
        self._hypothesis = {}
        self.significance_level = significance_level
        self.mh_correction_method = correction_method

    def add_hypothesis(self, agg, metrics, h):
        self._hypothesis[(agg, metrics)] = h

    def get_hypothesis(self, agg, metrics):
        self._hypothesis[(agg, metrics)]

    def set_multihypothesis_method(self, correction_method):
        self.mh_correction_method = correction_method

