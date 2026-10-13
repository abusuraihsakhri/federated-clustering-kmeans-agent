"""Deterministic, in-process simulation of federated Lloyd k-means.

Each site's assignment step contributes only cluster sums, counts and an inertia
sum to the round-level aggregator. This is NOT secure aggregation or
differential privacy: initial centroids and aggregates can disclose information.
Passing raw site records to this function is a simulation, not private transport.
"""
import math
from typing import Any


def _vector(values: Any, dimensions: int | None = None) -> list[float]:
    if not isinstance(values, (list, tuple)) or not values:
        raise ValueError("Each feature vector must be a nonempty list")
    if dimensions is not None and len(values) != dimensions:
        raise ValueError("Feature dimensions must match initial centroids")
    if len(values) > 32:
        raise ValueError("Maximum feature dimension is 32")
    if any(isinstance(x, (bool, str, bytes)) or not isinstance(x, (int, float))
           or not math.isfinite(x) for x in values):
        raise ValueError("Feature values must be finite numbers")
    return [float(x) for x in values]


def _aggregate(sites, centroids):
    k, dimension = len(centroids), len(centroids[0])
    sums = [[0.0] * dimension for _ in range(k)]
    counts = [0] * k
    by_site = []
    inertia = 0.0
    for site in sites:
        local = [0] * k
        for point in site:
            distances = [sum((a - b) ** 2 for a, b in zip(point, center))
                         for center in centroids]
            choice = min(range(k), key=distances.__getitem__)
            if not math.isfinite(distances[choice]):
                raise ValueError("Squared distance overflow")
            counts[choice] += 1
            local[choice] += 1
            inertia += distances[choice]
            for j, coordinate in enumerate(point):
                sums[choice][j] += coordinate
                if not math.isfinite(sums[choice][j]):
                    raise ValueError("Cluster sum overflow")
        by_site.append(local)
    if not math.isfinite(inertia):
        raise ValueError("Inertia overflow")
    return sums, counts, by_site, inertia


def federated_kmeans(
    sites: list[list[list[float]]],
    initial_centroids: list[list[float]],
    max_iterations: int = 100,
    tolerance: float = 1e-6,
) -> dict[str, Any]:
    """Iterate aggregate-only centroid updates across independent local sites.

    Cluster numbering follows the supplied initial centroid order. Ties resolve
    to the first centroid; empty clusters retain their prior centroid.
    """
    if not isinstance(max_iterations, int) or isinstance(max_iterations, bool) or not 1 <= max_iterations <= 200:
        raise ValueError("max_iterations must be between 1 and 200")
    if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)) or not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be finite and nonnegative")
    if not isinstance(initial_centroids, (list, tuple)) or not 1 <= len(initial_centroids) <= 20:
        raise ValueError("Supply between 1 and 20 initial centroids")
    centroids = [_vector(center) for center in initial_centroids]
    dimension = len(centroids[0])
    if any(len(center) != dimension for center in centroids):
        raise ValueError("Centroid dimensions must match")
    if not isinstance(sites, (list, tuple)) or not 1 <= len(sites) <= 64:
        raise ValueError("Supply between 1 and 64 sites")
    clean_sites = []
    size = 0
    for site in sites:
        if not isinstance(site, (list, tuple)) or not site:
            raise ValueError("Each site must contain at least one observation")
        size += len(site)
        if size > 20000:
            raise ValueError("Maximum number of observations is 20000")
        clean_sites.append([_vector(point, dimension) for point in site])
    if size < len(centroids):
        raise ValueError("Number of observations must be at least number of clusters")

    converged = False
    for iteration in range(1, max_iterations + 1):
        sums, counts, _, _ = _aggregate(clean_sites, centroids)
        updated = [
            [value / counts[i] for value in sums[i]] if counts[i] else centroids[i][:]
            for i in range(len(centroids))
        ]
        if any(not math.isfinite(v) for center in updated for v in center):
            raise ValueError("Centroid update overflow")
        shift = max(math.dist(before, after) for before, after in zip(centroids, updated))
        centroids = updated
        if shift <= tolerance:
            converged = True
            break

    _, counts, by_site, inertia = _aggregate(clean_sites, centroids)
    return {
        "centroids": centroids,
        "counts": counts,
        "per_site_counts": by_site,
        "inertia": inertia,
        "iterations": iteration,
        "converged": converged,
    }
