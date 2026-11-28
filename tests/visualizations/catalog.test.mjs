import assert from "node:assert/strict";
import fs from "node:fs";
const source = fs.readFileSync("backend/app/visualizations.py", "utf8");
for (const chart of ["bar", "line", "area", "pie", "scatter", "radar", "heatmap", "funnel", "gauge", "treemap", "boxplot", "calendar"]) {
  assert.match(source, new RegExp(`["']${chart}["']`), `catalog missing ${chart}`);
}
assert.match(source, /fallback/);
assert.match(source, /accessibility/);
console.log("Visualization catalog contract passed");
