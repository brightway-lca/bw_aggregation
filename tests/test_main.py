import sys

import numpy as np
import pytest
from bw2calc import LCA
from bw2data import Database, databases, get_node
from bw2data.backends import SQLiteBackend

from bw_aggregation import AggregatedDatabase, ObsoleteAggregatedDatapackage
from bw_aggregation.errors import IncompatibleDatabase


def check_a_database_matrices_unaggregated(lca: LCA):
    node = get_node(database="a", code="2")
    rows, _ = lca.technosphere_matrix[:, lca.dicts.activity[node.id]].nonzero()
    assert rows.shape == (2,)
    assert lca.technosphere_matrix[:, lca.dicts.activity[node.id]].sum() == 2.5

    rows, _ = lca.biosphere_matrix[:, lca.dicts.activity[node.id]].nonzero()
    assert rows.shape == (1,)
    assert lca.biosphere_matrix[:, lca.dicts.activity[node.id]].sum() == 1


def check_b_database_matrices_unaggregated(lca: LCA):
    node = get_node(database="b", code="1")
    rows, _ = lca.technosphere_matrix[:, lca.dicts.activity[node.id]].nonzero()
    assert rows.shape == (3,)
    assert np.allclose(
        lca.technosphere_matrix[:, lca.dicts.activity[node.id]].sum(), 0.65
    )

    rows, _ = lca.biosphere_matrix[:, lca.dicts.activity[node.id]].nonzero()
    assert rows.shape == (1,)
    assert lca.biosphere_matrix[:, lca.dicts.activity[node.id]].sum() == 7


def check_a_database_matrices_aggregated(lca: LCA):
    node = get_node(database="a", code="2")
    rows, _ = lca.technosphere_matrix[:, lca.dicts.activity[node.id]].nonzero()
    assert rows.shape == (1,)
    assert lca.technosphere_matrix[:, lca.dicts.activity[node.id]].sum() == 1

    rows, _ = lca.biosphere_matrix[:, lca.dicts.activity[node.id]].nonzero()
    assert rows.shape == (2,)
    assert lca.biosphere_matrix[:, lca.dicts.activity[node.id]].sum() != 1


def check_b_database_matrices_aggregated(lca: LCA):
    node = get_node(database="b", code="1")
    rows, _ = lca.technosphere_matrix[:, lca.dicts.activity[node.id]].nonzero()
    assert rows.shape == (1,)
    assert lca.technosphere_matrix[:, lca.dicts.activity[node.id]].sum() == 1

    rows, _ = lca.biosphere_matrix[:, lca.dicts.activity[node.id]].nonzero()
    assert rows.shape == (2,)
    assert lca.biosphere_matrix[:, lca.dicts.activity[node.id]].sum() != 7


@pytest.mark.skipif(
    sys.platform.startswith("win"), reason="Error on cleanup deleting tmpdir"
)
def test_convert_existing(background):
    AggregatedDatabase.convert_existing("a")
    assert databases["a"]["backend"] == "aggregated"
    assert databases["a"]["aggregation_calculation_time"]
    assert databases["a"]["aggregation_calculation_timestamp"]
    assert databases["a"]["aggregation_use_in_calculation"]


def test_different_matrices_when_aggregated(background):
    node = get_node(database="a", code="2")
    lca = LCA({node: 1}, method=("m",))
    lca.lci()
    lca.lcia()
    check_a_database_matrices_unaggregated(lca)

    AggregatedDatabase.convert_existing("a")
    lca = LCA({node: 1}, method=("m",))
    lca.lci()
    lca.lcia()
    check_a_database_matrices_aggregated(lca)


def test_different_matrices_when_aggregated_in_supply_chain(background):
    node = get_node(database="b", code="2")
    lca = LCA({node: 1}, method=("m",))
    lca.lci()
    lca.lcia()
    check_a_database_matrices_unaggregated(lca)

    AggregatedDatabase.convert_existing("a")
    lca = LCA({node: 1}, method=("m",))
    lca.lci()
    lca.lcia()
    check_a_database_matrices_aggregated(lca)


def test_same_score_when_aggregated(background):
    node = get_node(database="a", code="3")
    lca = LCA({node: 1}, method=("m",))
    lca.lci()
    lca.lcia()
    expected = lca.score

    AggregatedDatabase.convert_existing("a")
    lca = LCA({node: 1}, method=("m",))
    lca.lci()
    lca.lcia()
    result = lca.score

    print(expected, result)
    assert np.allclose(expected, result)


def test_same_score_when_aggregated_nonunitary_production(background):
    node = get_node(database="a", code="2")
    lca = LCA({node: 1}, method=("m",))
    lca.lci()
    lca.lcia()
    expected = lca.score

    AggregatedDatabase.convert_existing("a")
    lca = LCA({node: 1}, method=("m",))
    lca.lci()
    lca.lcia()
    result = lca.score

    print(expected, result)
    assert np.allclose(expected, result)


def test_same_score_when_aggregated_in_supply_chain(background):
    node = get_node(database="c", code="1")
    lca = LCA({node: 1}, method=("m",))
    lca.lci()
    lca.lcia()
    expected = lca.score

    AggregatedDatabase.convert_existing("a")
    lca = LCA({node: 1}, method=("m",))
    lca.lci()
    lca.lcia()
    result = lca.score

    print(expected, result)
    assert np.allclose(expected, result)


def test_same_score_when_multiple_aggregated_in_supply_chain(background):
    node = get_node(database="c", code="1")
    lca = LCA({node: 1}, method=("m",))
    lca.lci()
    lca.lcia()
    expected = lca.score

    check_a_database_matrices_unaggregated(lca)
    check_b_database_matrices_unaggregated(lca)

    AggregatedDatabase.convert_existing("a")
    AggregatedDatabase.convert_existing("b")

    lca = LCA({node: 1}, method=("m",))
    lca.lci()
    lca.lcia()

    print(lca.technosphere_matrix.todense())
    print(lca.biosphere_matrix.todense())

    check_a_database_matrices_aggregated(lca)
    check_b_database_matrices_aggregated(lca)

    result = lca.score
    print(expected, result)
    assert np.allclose(expected, result)


def test_same_score_when_all_aggregated_in_supply_chain(background):
    node = get_node(database="c", code="1")
    lca = LCA({node: 1}, method=("m",))
    lca.lci()
    lca.lcia()
    expected = lca.score

    check_a_database_matrices_unaggregated(lca)
    check_b_database_matrices_unaggregated(lca)

    AggregatedDatabase.convert_existing("a")
    AggregatedDatabase.convert_existing("b")
    AggregatedDatabase.convert_existing("c")

    lca = LCA({node: 1}, method=("m",))
    lca.lci()
    lca.lcia()

    check_a_database_matrices_aggregated(lca)
    check_b_database_matrices_aggregated(lca)

    result = lca.score
    print(expected, result)
    assert np.allclose(expected, result)


def test_outdated_when_database_changes(background):
    AggregatedDatabase.convert_existing("a")
    db = Database("a")

    node = get_node(database="a", code="1")
    node["name"] = "foo"
    node.save()

    with pytest.raises(ObsoleteAggregatedDatapackage):
        db.datapackage()

    db.refresh()
    assert db.datapackage()


def test_outdate_when_supply_chain_changes(background):
    AggregatedDatabase.convert_existing("b")
    db = Database("b")

    node = get_node(database="a", code="1")
    node["name"] = "foo"
    node.save()

    with pytest.raises(ObsoleteAggregatedDatapackage):
        db.datapackage()

    db.refresh()
    assert db.datapackage()


def test_outdate_when_aggregated_supply_chain_changes(background):
    AggregatedDatabase.convert_existing("a")
    AggregatedDatabase.convert_existing("b")
    db = Database("b")

    node = get_node(database="a", code="1")
    node["name"] = "foo"
    node.save()

    with pytest.raises(ObsoleteAggregatedDatapackage):
        db.datapackage()

    Database("a").refresh()
    db.refresh()
    assert db.datapackage()


def test_bw2data_database_correct_subclass(background):
    assert isinstance(Database("a"), SQLiteBackend)
    assert not isinstance(Database("a"), AggregatedDatabase)

    AggregatedDatabase.convert_existing("a")

    assert isinstance(Database("a"), AggregatedDatabase)


def test_refresh_all(background):
    AggregatedDatabase.convert_existing("a")
    AggregatedDatabase.convert_existing("b")

    node = get_node(database="a", code="1")
    node["name"] = "foo"
    node.save()

    node = get_node(database="b", code="1")
    node["name"] = "foo"
    node.save()

    assert not Database("a").aggregation_datapackage_valid()
    assert not Database("b").aggregation_datapackage_valid()

    AggregatedDatabase.refresh_all()

    assert Database("a").aggregation_datapackage_valid()
    assert Database("b").aggregation_datapackage_valid()


def test_incompatible_database_only_biosphere_flows(background):
    with pytest.raises(IncompatibleDatabase):
        AggregatedDatabase.convert_existing("bio")
