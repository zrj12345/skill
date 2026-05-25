---
name: iot-site-detail-integration
description: Use when working on SMARTLINK/iot-sys and iot-web-v2 site detail pages, especially /site-detail?id=..., to verify and fix frontend-backend API integration, duplicate requests, status enum fallback, DB-only mock validation, friendly error toasts, Chrome regression, and endpoint latency targets.
---

# IoT Site Detail Integration

Use this skill for site detail page work that spans `iot-sys` backend and `iot-web-v2` frontend. Treat the page as an integration surface: verify data source, request count, parameters, response rendering, latency, error UX, and product-scope alignment before editing.

## Required Context

- Backend repo: `C:\Users\1\Documents\aircloud\iot-sys`
- Frontend repo: `C:\Users\1\Documents\aircloud\iot-web-v2`
- Baseline plan: `C:\Users\1\Documents\aircloud\附加的功能清单及计划.md`
- Main analysis doc: `iot-sys/troubleshot/site_detail_page_integration_analysis.md`
- Pitfall log: `iot-sys/troubleshot/站点详情页踩坑记录.md`
- Browser target example: `http://localhost:3010/site-detail?id=23`

When modifying backend code, follow `iot-sys/AGENTS.md`: search for same-pattern issues globally, prefer reusable helpers, preserve API semantics, and record impact/verification.

## Workflow

1. Pull latest code in both repos before editing.
2. Read baseline docs, current trouble docs, and the relevant frontend/backend code.
3. Confirm the product scope. If Figma or the baseline plan does not cover a tab, keep it disabled unless the user explicitly reopens that scope.
4. Audit requests for each tab: initial page, monitoring center, device list, alarms, maintenance, data query, and disabled tabs.
5. Fix the smallest global pattern, not only the visible page symptom. For example, status enum fixes should align proto/model/biz/data/frontend maps.
6. Validate with tests, local runtime, Chrome, backend logs, and docs.
7. Commit and push both repos when a coherent stage is complete.

## Integration Checks

For each page or sub-tab, answer these before calling the work done:

- Is displayed data from a real backend API, not a new frontend/backend code mock?
- Are request parameters aligned with proto and backend types?
- Is the response rendered with correct field names, including snake_case/camelCase normalization if needed?
- Are enum values and fallback labels correct for unknown/empty states?
- Are duplicate requests avoided or justified?
- Are technical backend errors sanitized before Toast display?
- Are disabled tabs truly disabled, with no component mount and no network request?
- Are interface timings under 200ms, except documented expensive time-series/statistical paths?

## Request Simplification Pattern

Use this pattern for repeated device/site data fetches:

1. Let the first real table request return a complete snapshot only when it is unfiltered and covers `total`.
2. Cache that snapshot in the parent page.
3. Pass the snapshot to sibling tabs that need the same option set.
4. If a tab is entered directly and no complete snapshot exists, perform one lazy full request with explicit `pageNum` and `pageSize`.
5. Do not restore broad global list requests such as product category list when the scoped site-device API can return the needed display fields.

For data query specifically, derive device type options from site devices using backend-returned `productCategory.name` or parent category name. If only IDs are returned, fix the scoped backend response instead of hardcoding labels in the frontend.

## Backend Patterns

- Fix relation table names by using existing model constants where available.
- Always include soft-delete predicates when querying relation tables.
- Batch collect IDs first, then batch query, then map results back.
- Avoid N+1 lookups for gateways, collect templates, variables, locations, and status data.
- Provide explicit device state fallback:
  - online: `1`
  - offline: `2`
  - fault normal: `1`
  - fault active: `2`
  - unknown only when the source is genuinely unknown
- Derive site health status from batch counts through a single helper.
- Remove stdout prints from hot paths; use structured logs only when useful.
- Keep time-series/statistics optimizations separate when they require larger storage or aggregation design.

## Mock Data Rules

- Prefer DB-only mock SQL for validation.
- Do not add task-specific frontend code mocks or backend response mocks.
- Existing historical mocks outside the task scope may remain unchanged.
- Never mix real site data and newly seeded validation mock data in the same page instance.
- DB mock SQL must be idempotent, use fixed IDs, and skip or clean itself when the target site is already real business data.

## Chrome Regression

Use Chrome when requested or when verifying local UI behavior. Validate:

- Page opens without login redirect in the current authenticated session.
- Console error count is zero.
- Available tabs switch and render expected data or empty states.
- Disabled tabs keep `is-disabled`; clicking them does not change the active tab.
- Monitoring cycle switches such as today/week/month/year do not leave stale loading or overwrite newer data.
- Data query can select a device, load variables, query history, and render a chart without technical error Toast.

If Chrome's page execution context cannot expose request APIs or `performance`, use backend operation logs as the request-count and timing authority.

## Validation Commands

Backend:

```powershell
gofmt -w <edited-go-files>
go test ./...
go build -o .tmp\iot_sys_site_detail_verify.exe .\cmd\micro
```

Frontend:

```powershell
npx vue-tsc --noEmit
npm run build
```

If `npm run build` fails due to an unrelated existing dependency, record the exact unresolved import and keep the site-detail typecheck/browser evidence separate.

Useful backend log check:

```powershell
Select-String -Path .tmp\site-detail-verify-final.out.log -Pattern '/v1/equipmentGroup/equipment/list|/v1/equipmentGroup/statisticsHistory|/v1/equipmentGroup/info/23|/v1/equipmentEvent/list|/v1/maintenance/records/list|/v1/equipment/history|/v1/variable/list'
```

## Documentation Requirements

Update the pitfall log whenever a blocker or scope decision appears. Record:

- Which claim came from earlier analysis and whether it is still true.
- Which files and interfaces changed.
- Request path, parameters, response summary, and latency.
- Why any endpoint above 200ms is deferred.
- Whether DB mock seeded data, skipped seeding, or cleaned stale mock rows.
- Which local artifacts were intentionally not committed.
