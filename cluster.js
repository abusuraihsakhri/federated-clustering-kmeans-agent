"use strict";

/* Aggregate-only Lloyd updates in a single browser process, not a private FL transport. */
function federatedKmeans(input) {
  if (!input || typeof input !== "object" || Array.isArray(input)) throw Error("Expected a JSON object.");
  const {sites, initial_centroids: initial} = input;
  const iterations = input.max_iterations ?? 100;
  const tolerance = input.tolerance ?? 1e-6;
  if (!Number.isInteger(iterations) || iterations < 1 || iterations > 200) throw Error("max_iterations must be 1–200.");
  if (typeof tolerance !== "number" || !Number.isFinite(tolerance) || tolerance < 0) throw Error("tolerance must be a finite nonnegative number.");
  if (!Array.isArray(initial) || initial.length < 1 || initial.length > 20) throw Error("Supply 1–20 initial centroids.");
  function vector(v, dimension) {
    if (!Array.isArray(v) || !v.length || v.length > 32) throw Error("Each observation must have 1–32 numeric features.");
    if (dimension !== undefined && v.length !== dimension) throw Error("Feature dimensions must match.");
    if (!v.every(x => typeof x === "number" && Number.isFinite(x))) throw Error("Feature values must be finite numbers.");
    return v.slice();
  }
  let centers = initial.map(v => vector(v));
  const dim = centers[0].length;
  if (!centers.every(v => v.length === dim)) throw Error("Centroid dimensions must match.");
  if (!Array.isArray(sites) || sites.length < 1 || sites.length > 64) throw Error("Supply 1–64 sites.");
  let observations = 0;
  const cleanSites = sites.map(site => {
    if (!Array.isArray(site) || !site.length) throw Error("Every site must contain observations.");
    observations += site.length;
    if (observations > 20000) throw Error("Maximum 20000 observations.");
    return site.map(row => vector(row, dim));
  });
  if (observations < centers.length) throw Error("Observations must outnumber or equal clusters.");
  function aggregate(current) {
    const sums = current.map(() => Array(dim).fill(0));
    const counts = current.map(() => 0);
    const per_site_counts = [];
    let inertia = 0;
    for (const site of cleanSites) {
      const local = current.map(() => 0);
      for (const point of site) {
        let best = 0, bestDistance = Infinity;
        for (let k = 0; k < current.length; k++) {
          let distance = 0;
          for (let d = 0; d < dim; d++) distance += (point[d] - current[k][d]) ** 2;
          if (distance < bestDistance) { best = k; bestDistance = distance; }
        }
        if (!Number.isFinite(bestDistance)) throw Error("Squared distance overflow.");
        inertia += bestDistance;
        counts[best]++;
        local[best]++;
        for (let d = 0; d < dim; d++) {
          sums[best][d] += point[d];
          if (!Number.isFinite(sums[best][d])) throw Error("Cluster sum overflow.");
        }
      }
      per_site_counts.push(local);
    }
    if (!Number.isFinite(inertia)) throw Error("Inertia overflow.");
    return {sums, counts, per_site_counts, inertia};
  }
  let converged = false, count = 0;
  for (let i = 1; i <= iterations; i++) {
    const aggregation = aggregate(centers);
    const updated = centers.map((old, k) => aggregation.counts[k] ?
      aggregation.sums[k].map(v => v / aggregation.counts[k]) : old.slice());
    let maxShift = 0;
    for (let k = 0; k < centers.length; k++) {
      let shift = 0;
      for (let d = 0; d < dim; d++) shift += (updated[k][d] - centers[k][d]) ** 2;
      maxShift = Math.max(maxShift, Math.sqrt(shift));
    }
    if (!Number.isFinite(maxShift)) throw Error("Centroid update overflow.");
    centers = updated;
    count = i;
    if (maxShift <= tolerance) { converged = true; break; }
  }
  const final = aggregate(centers);
  return {centroids: centers, counts: final.counts, per_site_counts: final.per_site_counts,
    inertia: final.inertia, iterations: count, converged};
}

if (typeof document !== "undefined") {
  const $ = id => document.getElementById(id);
  const example = $("dataset").value;
  let lastResult = null;
  function td(row, value) {
    const cell = document.createElement("td");
    cell.textContent = String(value);
    row.append(cell);
  }
  function showResults(r) {
    $("iterations").textContent = String(r.iterations);
    $("converged").textContent = r.converged ? "Yes" : "No";
    $("inertia").textContent = r.inertia.toLocaleString(undefined, {maximumSignificantDigits: 6});
    $("observations").textContent = String(r.counts.reduce((a, b) => a + b, 0));
    $("centroids").replaceChildren();
    r.centroids.forEach((center, i) => {
      const row = document.createElement("tr");
      td(row, i + 1);
      td(row, center.map(n => Number(n.toPrecision(8))).join(", "));
      td(row, r.counts[i]);
      $("centroids").append(row);
    });
    $("siteCounts").replaceChildren();
    r.per_site_counts.forEach((counts, i) => {
      const row = document.createElement("tr");
      td(row, i + 1);
      td(row, counts.join(" / "));
      $("siteCounts").append(row);
    });
    $("export").disabled = false;
  }
  $("run").addEventListener("click", () => {
    $("error").textContent = "";
    try {
      lastResult = federatedKmeans(JSON.parse($("dataset").value));
      showResults(lastResult);
    } catch (error) {
      lastResult = null;
      $("export").disabled = true;
      $("error").textContent = error instanceof SyntaxError ? "Invalid JSON: " + error.message : error.message;
    }
  });
  $("example").addEventListener("click", () => {
    $("dataset").value = example;
    $("run").click();
  });
  $("upload").addEventListener("change", async event => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      if (file.size > 2_000_000) throw Error("JSON input must be smaller than 2 MB.");
      const contents = await file.text();
      JSON.parse(contents);
      $("dataset").value = contents;
      $("run").click();
    } catch (error) { $("error").textContent = error.message; }
    finally { event.target.value = ""; }
  });
  $("export").addEventListener("click", () => {
    if (!lastResult) return;
    const blob = new Blob([JSON.stringify(lastResult, null, 2) + "\n"], {type: "application/json"});
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "federated-kmeans-results.json";
    link.click();
    URL.revokeObjectURL(url);
  });
  $("run").click();
}
if (typeof module !== "undefined" && module.exports) module.exports = {federatedKmeans};
