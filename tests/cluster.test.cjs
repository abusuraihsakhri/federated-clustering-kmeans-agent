"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const {federatedKmeans} = require("../cluster.js");

test("two-site means and inertia", () => {
  const actual = federatedKmeans({
    sites: [[[0, 0], [0, 2]], [[10, 10], [10, 12]]],
    initial_centroids: [[0, 0], [10, 10]]
  });
  assert.deepEqual(actual.centroids, [[0, 1], [10, 11]]);
  assert.deepEqual(actual.counts, [2, 2]);
  assert.deepEqual(actual.per_site_counts, [[2, 0], [0, 2]]);
  assert.equal(actual.inertia, 4);
  assert.equal(actual.converged, true);
});
test("retains an empty cluster", () => {
  assert.deepEqual(federatedKmeans({sites: [[[0], [0]]], initial_centroids: [[0], [10]]}).centroids, [[0], [10]]);
});
test("rejects malformed data", () => {
  for (const data of [
    {sites: [], initial_centroids: [[0]]},
    {sites: [[[0]]], initial_centroids: [[0, 1]]},
    {sites: [[[Infinity]]], initial_centroids: [[0]]},
    {sites: [[[0]]], initial_centroids: [[0]], tolerance: -1},
    {sites: [[[0]]], initial_centroids: [[0]], max_iterations: 0},
  ]) assert.throws(() => federatedKmeans(data));
});
