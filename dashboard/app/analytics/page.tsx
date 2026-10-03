/** Analytics — call volume, intents, latency p50/p95, cost breakdown. */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export const dynamic = "force-dynamic";

export default function AnalyticsPage() {
  // Charts go here once the /metrics Prometheus data is exposed. Suggested
  // initial set:
  //   - Calls per hour × weekday (heatmap, staffing insight)
  //   - Top intents and top questions
  //   - Booking conversion rate
  //   - Transfer + abandonment reasons
  //   - Latency percentiles (p50, p95) by stage
  //   - Cost breakdown by component
  return (
    <div className="space-y-6 p-6">
      <h1 className="text-3xl font-semibold tracking-tight">Analytics</h1>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Call volume</CardTitle>
            <CardDescription>By hour and weekday</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            (Recharts chart placeholder)
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Cost breakdown</CardTitle>
            <CardDescription>Telephony, STT, TTS, LLM</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            (Recharts chart placeholder)
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Latency percentiles</CardTitle>
            <CardDescription>p50, p95, per stage</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            (Recharts chart placeholder)
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top intents</CardTitle>
            <CardDescription>Booking, FAQ, complaint, sales</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            (Recharts chart placeholder)
          </CardContent>
        </Card>
      </div>
    </div>
  );
}