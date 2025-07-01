from collections import Counter
from collections.abc import Iterable
from typing import Optional

from bw2data import Database, databases, labels


def check_processes_in_database(database_name: str) -> bool:
    """Check to make sure database is usable for aggregated calculations."""
    if database_name not in databases:
        raise KeyError(f"{database_name} not in databases")
    return check_processes_in_data(Database(database_name))


def check_processes_in_data(objects: Iterable) -> bool:
    """Check if any object in the input data has type `process`"""
    return any(
        obj.get("type", labels.process_node_default) in labels.process_node_types
        for obj in objects
    )


def get_process_type_counts(database_name: str) -> dict[Optional[str], int]:
    """Get count of each process type in database"""
    if database_name not in databases:
        raise KeyError(f"{database_name} not in databases")
    return dict(
        Counter([obj.get("type") for obj in Database(database_name)]).most_common()
    )
