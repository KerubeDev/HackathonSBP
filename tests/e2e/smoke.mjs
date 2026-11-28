const api = process.env.API_URL || "http://localhost:8000";
const frontend = process.env.FRONTEND_URL || "http://localhost:3001";
const health = await fetch(`${api}/healthz`);
if (!health.ok) throw new Error(`Backend health failed: ${health.status}`);
const response = await fetch(`${api}/api/agent/run`, {
  method: "POST",
  headers: {"content-type": "application/json"},
  body: JSON.stringify({query: "Compare value by region", api_version: "v1"})
});
if (!response.ok) throw new Error(`Run failed: ${response.status}`);
const started = await response.json();
let result = started;
for (let i = 0; i < 30 && !["completed", "failed"].includes(result.status); i++) {
  await new Promise(resolve => setTimeout(resolve, 250));
  result = await fetch(`${api}${started.poll_url}`).then(r => r.json());
}
if (result.status !== "completed") throw new Error(`Run did not complete: ${result.status}`);
if (!result.result?.data?.length || !result.result.chart_config) throw new Error("Missing result data or chart");
const page = await fetch(frontend);
if (!page.ok) throw new Error(`Frontend failed: ${page.status}`);
console.log("E2E smoke passed", started.run_id);
