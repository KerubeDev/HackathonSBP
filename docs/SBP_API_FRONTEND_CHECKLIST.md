# SBP API ↔ Frontend checklist

## Connection foundation

- [x] `NEXT_PUBLIC_API_URL` is documented and used by one API client.
- [x] API errors have one normalized frontend shape.
- [ ] Backend health endpoint is reachable from the frontend runtime.

## Public profile

- [ ] Profile capabilities load from `GET /api/profile`.
- [x] Rankings load from `GET /api/rankings`.
- [ ] Chart data loads from `GET /api/charts/rankings`.
- [ ] Quality metadata loads from `GET /api/quality/{period}`.
- [ ] Subactivities load from `GET /api/rankings/subactivities`.
- [ ] CSV/JSON/XLSX/PDF exports are linked.

## Analyst profile

- [x] Comparisons load from `GET /api/comparisons`.
- [ ] Movement states and errors render.
- [ ] Agent catalog loads from `GET /api/agents`.
- [ ] Ask-to runs use the existing run/status contract.

## Administrator profile

- [x] AT03 preview uses `POST /api/rankings/preview`.
- [ ] Preview confirmation uses `POST /api/rankings/confirm`.
- [ ] Cancellation uses `POST /api/rankings/cancel`.
- [ ] Load history uses `GET /api/rankings/loads`.
- [ ] Administrator errors and forbidden responses render.

## Verification

- [ ] Frontend production build passes.
- [ ] Backend API contract tests pass.
- [ ] Browser smoke test covers each profile.
