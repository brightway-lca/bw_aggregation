import pytest
from bw2data import Database, labels

from bw_aggregation.utils import (
    check_processes_in_data,
    check_processes_in_database,
    get_process_type_counts,
)


def test_check_processes_in_database(background):
    assert check_processes_in_database("a")
    assert not check_processes_in_database("bio")
    with pytest.raises(KeyError):
        check_processes_in_database("missing")


def test_get_process_type_counts(background):
    assert get_process_type_counts("a") == {
        labels.chimaera_node_default: 3,
        "emission": 1,
    }
