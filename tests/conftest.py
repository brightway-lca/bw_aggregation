"""Fixtures for bw_aggregation"""

import pytest
from bw2data import Database, Method, labels
from bw2data.tests import bw2test


@pytest.fixture
@bw2test
def background():
    bio_data = {
        ("bio", "alpha"): {"exchanges": [], "type": labels.biosphere_node_default},
        ("bio", "beta"): {"exchanges": [], "type": labels.biosphere_node_default},
    }
    Database("bio").write(bio_data)

    cfs = [
        (("bio", "alpha"), 4),
        (("bio", "beta"), -2),
    ]

    Method(("m",)).register()
    Method(("m",)).write(cfs)

    a_data = {
        ("a", "1"): {
            "exchanges": [
                {
                    "amount": 1,
                    "type": labels.production_edge_default,
                    "input": ("a", "1"),
                },
                {
                    "amount": 0.1,
                    "type": labels.consumption_edge_default,
                    "input": ("a", "3"),
                },
                {
                    "amount": 7,
                    "type": labels.biosphere_edge_default,
                    "input": ("bio", "beta"),
                },
            ],
        },
        ("a", "2"): {
            "exchanges": [
                {
                    "amount": 0.5,
                    "type": labels.production_edge_default,
                    "input": ("a", "2"),
                },
                {
                    "amount": -2,
                    "type": labels.consumption_edge_default,
                    "input": ("a", "1"),
                },
                {
                    "amount": 1,
                    "type": labels.biosphere_edge_default,
                    "input": ("bio", "alpha"),
                },
            ],
        },
        ("a", "3"): {
            "exchanges": [
                {
                    "amount": 1,
                    "type": labels.production_edge_default,
                    "input": ("a", "3"),
                },
                {
                    "amount": 3,
                    "type": labels.consumption_edge_default,
                    "input": ("a", "1"),
                },
                {
                    "amount": 2,
                    "type": labels.consumption_edge_default,
                    "input": ("a", "2"),
                },
                {
                    "amount": 2,
                    "type": labels.biosphere_edge_default,
                    "input": ("bio", "alpha"),
                },
                {
                    "amount": 5,
                    "type": labels.biosphere_edge_default,
                    "input": ("bio", "beta"),
                },
            ],
        },
        ("a", "4"): {
            "name": "CO2",
            "type": labels.biosphere_node_default,
            "exchanges": [],
        },
    }
    Database("a").write(a_data)

    b_data = {
        ("b", "1"): {
            "exchanges": [
                {
                    "amount": 1,
                    "type": labels.production_edge_default,
                    "input": ("b", "1"),
                },
                {
                    "amount": 0.1,
                    "type": labels.consumption_edge_default,
                    "input": ("b", "2"),
                },
                {
                    "amount": 0.25,
                    "type": labels.consumption_edge_default,
                    "input": ("a", "3"),
                },
                {
                    "amount": 7,
                    "type": labels.biosphere_edge_default,
                    "input": ("bio", "beta"),
                },
            ],
        },
        ("b", "2"): {
            "exchanges": [
                {
                    "amount": 0.5,
                    "type": labels.production_edge_default,
                    "input": ("b", "2"),
                },
                {
                    "amount": -2,
                    "type": labels.consumption_edge_default,
                    "input": ("a", "1"),
                },
                {
                    "amount": 5,
                    "type": labels.biosphere_edge_default,
                    "input": ("bio", "beta"),
                },
            ],
        },
    }
    Database("b").write(b_data)

    c_data = {
        ("c", "1"): {
            "exchanges": [
                {
                    "amount": 1,
                    "type": labels.production_edge_default,
                    "input": ("c", "1"),
                },
                {
                    "amount": 0.1,
                    "type": labels.consumption_edge_default,
                    "input": ("a", "3"),
                },
                {
                    "amount": 0.2,
                    "type": labels.consumption_edge_default,
                    "input": ("b", "2"),
                },
                {
                    "amount": 0.3,
                    "type": labels.consumption_edge_default,
                    "input": ("c", "2"),
                },
                {
                    "amount": 1,
                    "type": labels.biosphere_edge_default,
                    "input": ("bio", "beta"),
                },
            ],
        },
        ("c", "2"): {
            "exchanges": [
                {
                    "amount": 0.5,
                    "type": labels.production_edge_default,
                    "input": ("c", "2"),
                },
                {
                    "amount": -0.2,
                    "type": labels.consumption_edge_default,
                    "input": ("b", "1"),
                },
                {
                    "amount": 2,
                    "type": labels.biosphere_edge_default,
                    "input": ("bio", "alpha"),
                },
            ],
        },
    }
    Database("c").write(c_data)
