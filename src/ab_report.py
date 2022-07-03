class ABReport:
    def __init__(self, aggregations, ab_hypothesis_manager):
        self.aggregations = aggregations
        self.ab_hm = ab_hypothesis_manager

    def prepare_report(self):
        for agg in self.aggregations:
            print('agg: ', agg.get_full_name())
            for metrics in agg.get_metrics_list():
                print(
                    'metrics: ',
                    metrics.get_name(),
                    'hypothesis',
                    self.ab_hm.get_hypothesis(agg, metrics)
                )
                # print()

    def display(self):
        self.prepare_report()
