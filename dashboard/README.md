# Receptionist dashboard

Next.js 14 App Router + Tailwind + shadcn/ui + Recharts + NextAuth.

## Pages

| Route | Module |
|---|---|
| `/` | Overview — calls today, bookings, cost, alerts |
| `/calls` | Calls list |
| `/calls/[id]` | Call detail — audio + transcript + tool calls + costs |
| `/messages` | Messages inbox |
| `/appointments` | Appointments |
| `/contacts` | Contacts, tags, block list |
| `/config` | Prompt versions, business facts, voice |
| `/knowledge` | FAQ entries + knowledge gaps |
| `/analytics` | Charts |
| `/settings` | Users, channels, retention, audit |
| `/login` | Sign in |

## Run locally

```bash
cd dashboard
npm install
cp .env.example .env.local
npm run dev
```

The dev server proxies `/api/proxy/*` to the FastAPI service. See
`next.config.js`.

## What is NOT implemented yet

- All shadcn primitives beyond Card / Input / Button / Badge. Add more with
  `npx shadcn-ui@latest add ...` as needed.
- NextAuth provider wiring (signup + login currently hit `/auth/signup` and
  `/auth/login` directly).
- The form-driven editors for prompt sections, business facts, knowledge
  items. Tables read from the api; writes go through server actions.
- Real charts in `/analytics`. The data endpoints exist; they just need to be
  rendered with Recharts.