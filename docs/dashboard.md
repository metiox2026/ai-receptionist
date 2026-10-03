# Dashboard

The Next.js 14 dashboard. Lives in `dashboard/`. Runs against the FastAPI
backend at `NEXT_PUBLIC_API_URL`.

## Modules

| Route | Section | Source |
|---|---|---|
| `/` | Overview | `/calls`, `/healthz` |
| `/calls` | Calls list | `/calls` |
| `/calls/[id]` | Call detail | `/calls/[id]` |
| `/messages` | Messages inbox | `/messages` |
| `/appointments` | Appointments | `/appointments` |
| `/contacts` | Contacts + block list | `/contacts` |
| `/config` | Prompt versions + voice | `/config/prompt-versions` |
| `/knowledge` | FAQ + knowledge gaps | `/knowledge` |
| `/analytics` | Charts | Prometheus metrics (TBD) |
| `/quality` | Review queue + regression results | `/quality` (TBD) |
| `/settings` | Users, channels, retention, audit | `/settings` (TBD) |

## Auth

Login lives at `/login`. For the scaffold, the form posts to `/auth/login`
on the API. NextAuth wires in once you need OAuth providers or session
refresh tokens.

## Adding a new module

1. Create the page at `app/<name>/page.tsx`.
2. Add a `nav` entry in `components/sidebar.tsx`.
3. Add the matching typed function in `lib/api.ts`.
4. If the API needs a new endpoint, add a router file under
   `api/routers/` and include it in `main.py`.

## What's implemented vs not

Implemented (read paths):

- Overview, Calls, Messages, Appointments, Contacts, Config,
  Knowledge, Analytics placeholder, Settings placeholder, Quality
  placeholder, Login.

Not implemented (write paths):

- Prompt version creation, knowledge item add/edit, contact block/unblock,
  appointment cancel, call flag, settings forms.

These are stubbed in the API routers; the dashboard pages read from the
existing GET endpoints and the write UI is left for Phase 1 work.