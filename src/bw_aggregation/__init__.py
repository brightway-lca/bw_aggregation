"""bw_aggregation."""

__all__ = (
    "__version__",
    "AggregatedDatabase",
    "AggregationContext",
    "ObsoleteAggregatedDatapackage",
    "Speedup",
)

__version__ = "1.2"


from bw2data.backends import Activity
from bw2data.subclass_mapping import (
    DATABASE_BACKEND_MAPPING,
    NODE_PROCESS_CLASS_MAPPING,
)

from .estimator import Speedup
from .main import AggregatedDatabase, ObsoleteAggregatedDatapackage
from .override import AggregationContext

DATABASE_BACKEND_MAPPING["aggregated"] = AggregatedDatabase
NODE_PROCESS_CLASS_MAPPING["aggregated"] = Activity
