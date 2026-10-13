"""Behavioral tests for actual federated Lloyd centroid aggregation."""
import math
import pytest
from fed_kmeans.clustering import federated_kmeans


def test_two_sites_two_clusters():
    result = federated_kmeans(
        sites=[[[0, 0], [0, 2]], [[10, 10], [10, 12]]],
        initial_centroids=[[0, 0], [10, 10]],
    )
    assert result["centroids"] == [[0, 1], [10, 11]]
    assert result["counts"] == [2, 2]
    assert result["per_site_counts"] == [[2, 0], [0, 2]]
    assert result["inertia"] == pytest.approx(4)
    assert result["converged"]
    assert result["iterations"] <= 3


def test_empty_cluster_is_retained():
    result = federated_kmeans([[[0], [0]]], [[0], [10]])
    assert result["centroids"] == [[0], [10]]
    assert result["counts"] == [2, 0]
    assert result["inertia"] == 0


@pytest.mark.parametrize("sites,centers", [
    ([], [[0]]),
    ([[]], [[0]]),
    ([[[0, 1]]], [[0]]),
    ([[[float("nan")]]], [[0]]),
    ([[[float("inf")]]], [[0]]),
    ([[[0]]], [[0, 0]]),
    ([[[0]]], [[0], [1]]),
    ([[[True]]], [[0]]),
    ([[[0]]], [[float("inf")]]),
])
def test_invalid_input(sites, centers):
    with pytest.raises(ValueError):
        federated_kmeans(sites, centers)


def test_iteration_and_tolerance_validation():
    with pytest.raises(ValueError):
        federated_kmeans([[[0]]], [[0]], max_iterations=0)
    with pytest.raises(ValueError):
        federated_kmeans([[[0]]], [[0]], tolerance=math.nan)
    with pytest.raises(ValueError):
        federated_kmeans([[[0]]], [[0]], tolerance=-1)
