from datetime import datetime as dt

from bw2data import databases
from bw2data.backends import SQLiteBackend
from bw_processing import (
    Datapackage,
    clean_datapackage_name,
    create_datapackage,
    load_datapackage,
)
from fs.zipfs import ZipFS

from .calculator import AggregationCalculator
from .errors import IncompatibleDatabase, ObsoleteAggregatedDatapackage
from .estimator import CalculationDifferenceEstimator, Speedup
from .override import AggregationContext, aggregation_override
from .utils import check_processes_in_data, check_processes_in_database


class AggregatedDatabase(SQLiteBackend):
    """A class which maintains two processed datapackages, and can use the aggregated datapackage
    for quicker calculations.

    An aggregated database only stores the *cumulative biosphere flows* of each unit process
    instead of its actual supply chain. Because it stores less information, it can't do graph
    traversal, Monte Carlo, or show any information on the processes in the supply chain causing
    impacts.

    Calculating aggregated emissions for every process in a database can be expensive. Therefore,
    this library in only useful for large background databases which do not change frequently.

    You can get an estimate of the speed increase possible for a given database with
    `AggregatedDatabase.estimate_speedup('<database name>')`.

    To create a new aggregated database, use `bw2data.Database('<name>', backend='aggregated')`.
    To convert an existing database, use `AggregatedDatabase.convert_existing()`.

    You can still do normal calculations with an aggregated database. To set the default
    calculation method to use the aggregated values, call `db.use_aggregated()` (where `db` is an
    instance of `AggregatedDatabase`). To set the default to use unit processes, call
    `db.use_aggregated(False)`.

    Stores configuration and log data in the `Database` metadata dictionary in the following keys:

    * `aggregation_calculation_time`: float. Time to last calculate aggregation in seconds.
    * `aggregation_calculation_timestamp`: TBD
    * `aggregation_use_in_calculation`: bool. Use the aggregated datapackage in calculations.

    """

    def aggregation_datapackage_valid(self) -> bool:
        """Check if the aggregation datapackage is still fresh.

        Checks whether any of the dependent databases have been changed since the
        aggregation datapackage was created."""
        databases.clean()

        if not self.metadata.get("aggregation_calculation_timestamp"):
            return False
        latest_change = max(
            [dt.fromisoformat(self.metadata["processed"])]
            + [
                dt.fromisoformat(databases[db]["processed"])
                for db in self.find_graph_dependents()
            ]
        )
        return (
            dt.fromisoformat(self.metadata["aggregation_calculation_timestamp"])
            >= latest_change
        )

    @staticmethod
    def estimate_speedup(database_name: str) -> Speedup:
        """Estimate how much quicker calculations could be when using aggregated emissions.

        Prints to `stdout` and return a float, the ratio of calculation speed with aggregation
        to speed without aggregation."""
        return CalculationDifferenceEstimator(database_name).difference()

    @staticmethod
    def convert_existing(database_name: str) -> None:
        """Convert a unit process database to an aggregated database."""
        if database_name not in databases:
            raise ValueError(f"Database '{database_name}' doesn't exist")
        if databases[database_name]["backend"] == "aggregated":
            print(f"Database '{database_name}' is already aggregated")
            return
        if not check_processes_in_database(database_name):
            raise IncompatibleDatabase(
                "This database only has biosphere flows, and can't be aggregated."
            )

        db = AggregatedDatabase(database_name)
        db.process_aggregated()
        databases[database_name]["backend"] = "aggregated"
        db.use_aggregated(True)

    def use_aggregated(self, default: bool = True) -> None:
        """Set default calculation to use (or not use) the aggregated emissions."""
        if default not in {True, False}:
            raise ValueError(f"`default` must be a boolean; got '{default}'")
        self.metadata["aggregation_use_in_calculation"] = default
        self._metadata.flush()

    def datapackage(self):
        """Pick the right datapackage depending on settings"""
        if (aggregation_override.global_override is True) or (
            aggregation_override.local_overrides.get(self.name, None) is True
        ):
            fp = self.filepath_aggregated()
        elif (aggregation_override.global_override is False) or (
            aggregation_override.local_overrides.get(self.name, None) is False
        ):
            fp = self.filepath_processed()
        else:
            fp = (
                self.filepath_aggregated()
                if self.metadata.get("aggregation_use_in_calculation")
                else self.filepath_processed()
            )
        with ZipFS(fp) as zip_fs:
            return load_datapackage(zip_fs)

    def filepath_aggregated(self):
        if not self.aggregation_datapackage_valid():
            MESSAGE = f"""Aggregated datapackage for database '{self.name}' is out of date.
    It needs to be recalculated with:

        import bw_aggregated as bwa
        bwa.AggregatedDatabase("{self.name}").process_aggregated()

    If you have mutual references in multiple aggregated databases, you can refresh all outdated 
    with:

        bwa.AggregatedDatabase.refresh_all()

    """
            raise ObsoleteAggregatedDatapackage(MESSAGE)

        return self.dirpath_processed() / self.filename_aggregated()

    def filename_aggregated(self):
        return clean_datapackage_name(self.filename + "aggregated.zip")

    def refresh(self) -> None:
        """Easy to remember shortcut for humans."""
        self.process_aggregated()

    @staticmethod
    def refresh_all() -> None:
        outdated_databases = [
            name
            for name, meta in databases.items()
            if meta["backend"] == "aggregated"
            and not AggregatedDatabase(name).aggregation_datapackage_valid()
        ]
        with AggregationContext(False):
            for db_name in outdated_databases:
                AggregatedDatabase(db_name).refresh()

    def write(self, data, process=True, searchable=True) -> None:
        if not check_processes_in_data(data.values()):
            raise IncompatibleDatabase(
                "This data only has biosphere flows, and can't be aggregated."
            )

        super().write(data=data, process=process, searchable=searchable)

        if process:
            self.process_aggregated()

    def process_aggregated(self, in_memory: bool = False) -> Datapackage:
        """Create structured arrays for the aggregated biosphere emissions, and for unitary production."""
        # Try to avoid race conditions - but no guarantee
        self.metadata["aggregation_calculation_timestamp"] = dt.now().isoformat()

        calculator = AggregationCalculator(self.name)
        calculator.calculate()

        dp = create_datapackage(
            fs=(
                None
                if in_memory
                else ZipFS(str(self.filepath_aggregated()), write=True)
            ),
            name=clean_datapackage_name(self.name),
            sum_intra_duplicates=True,
            sum_inter_duplicates=False,
        )
        self._add_inventory_geomapping_to_datapackage(dp=dp)

        dp.add_persistent_vector_from_iterator(
            matrix="biosphere_matrix",
            name=clean_datapackage_name(self.name + " biosphere matrix"),
            dict_iterator=calculator.biosphere_iterator,
        )
        dp.add_persistent_vector_from_iterator(
            matrix="technosphere_matrix",
            name=clean_datapackage_name(self.name + " technosphere matrix"),
            dict_iterator=calculator.technosphere_iterator,
        )
        if not in_memory:
            dp.finalize_serialization()
        return dp
