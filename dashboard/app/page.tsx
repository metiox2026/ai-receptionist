/** Overview — calls today, bookings, messages, transfers, cost, live status. */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

async function fetchStats() {
  // For now: a single /healthz call to prove the wiring works. Replace with a
  // dedicated /stats endpoint that aggregates today's metrics from Postgres.
  try {
    const health = await api.health();
    return { ok: health.ok, deps: health.dependencies };
  } catch {
    return { ok: false, deps: {} };
  }
}

export default async function OverviewPage() {
  const stats = await fetchStats();

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-semibold tracking-tight">Overview</h1>
        <div className="text-sm text-muted-foreground">
          Agent health: {stats.ok ? "OK" : "Unavailable"}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Stat label="Calls today" value="—" hint="Add /stats endpoint" />
        <Stat label="Bookings today" value="—" />
        <Stat label="Messages today" value="—" />
        <Stat label="Cost today" value="—" />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Live status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <Dependency label="Postgres" ok={stats.deps.db} />
            <Dependency label="Redis" ok={stats.deps.redis} />
            <p className="text-xs text-muted-foreground">
              Active calls, recent errors and p50/p95 latency will appear here
              once the stats endpoint exists.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Failed calls, high latency and cost spikes will be listed here.
              Wires up once the alerting job is built (Phase 4).
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-semibold">{value}</div>
        {hint ? <div className="text-xs text-muted-foreground">{hint}</div> : null}
      </CardContent>
    </Card>
  );
}

function Dependency({ label, ok }: { label: string; ok: boolean | undefined }) {
  return (
    <div className="flex items-center justify-between">
      <span>{label}</span>
      <span className={ok ? "text-green-600" : "text-red-600"}>{ok ? "OK" : "Down"}</span>
    </div>
  );
}