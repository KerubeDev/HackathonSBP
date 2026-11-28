import fs from "node:fs";
const page = fs.readFileSync("frontend/app/page.tsx", "utf8");
for (const required of ["htmlFor=", "aria-live", "role=\"alert\"", "<caption", "scope=\"col\""]) {
  if (!page.includes(required)) throw new Error(`Missing accessibility marker: ${required}`);
}
console.log("Static accessibility contract passed");
