from dataclasses import dataclass
from time import time

from bw2calc import LCA
from bw2data import Database, Node, prepare_lca_inputs

from .errors import IncompatibleDatabase
from .override import AggregationContext
from .utils import check_processes_in_database


@dataclass
class Speedup:
    database_name: str
    time_with_aggregation: float
    time_without_aggregation: float
    time_difference_absolute: float
    time_difference_relative: float


class CalculationDifferenceEstimator:
    def __init__(self, database_name: str):
        self.name = database_name
        self.db = Database(database_name)
        self.random_product = self.pick_random_product()

    def pick_random_product(self) -> Node:
        """Check database structure and pick random product"""
        if not check_processes_in_database(self.db.name):
            dataset_types_formatted = "\n\t".join(
                [
                    f"{a}: {b} objects"
                    for a, b in test_get_process_type_counts(self.db.name).items()
                ]
            )
            ERROR = f"""
    This database has the wrong kind of flows for an inventory calculation.
    It should have either only "process" flow types, or "process" and "product" flows.
    The following flows were found in database {self.db.name}: \n\t{dataset_types_formatted}
            """
            raise IncompatibleDatabase(ERROR)

        for ds in self.db:
            production = list([exc for exc in ds.production() if exc["amount"]])
            if len(production) == 1:
                return production[0].output

        ERROR = f"""
The database {self.db.name} has no processes with a single non-zero production exchange.
We can't find a suitable process to do the example calculations with.
        """
        raise IncompatibleDatabase(ERROR)

    def difference(self) -> Speedup:
        without = self.calculate_without_speedup()
        with_ = self.calculate_with_speedup()
        return Speedup(
            database_name=self.name,
            # Timer on Windows is coarse, could be zero for small databases
            time_difference_relative=(with_ / without if without > 0 else 0),
            time_difference_absolute=with_ - without,
            time_with_aggregation=with_,
            time_without_aggregation=without,
        )

    def calculate_with_speedup(self):
        from .main import AggregatedDatabase

        with AggregationContext({self.name: False}):
            fu, data_objs, _ = prepare_lca_inputs({self.random_product: 1})
            data_objs[-1] = AggregatedDatabase(self.name).process_aggregated(
                in_memory=True
            )

            start = time()
            lca = LCA(fu, data_objs=data_objs)
            lca.lci()
            end = time()

        return end - start

    def calculate_without_speedup(self):
        with AggregationContext({self.name: False}):
            fu, data_objs, _ = prepare_lca_inputs({self.random_product: 1})

            start = time()
            lca = LCA(fu, data_objs=data_objs)
            lca.lci()
            end = time()

        return end - start
