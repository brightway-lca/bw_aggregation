class IncompatibleDatabase(Exception):
    """Database can't be used for inventory calculations.

    Usually because it only has biosphere flows."""

    pass


class ObsoleteAggregatedDatapackage(Exception):
    """The results from this aggregated datapackage are obsolete"""

    pass
