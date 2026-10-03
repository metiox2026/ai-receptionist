/** Call detail — audio player, transcript synced to playback, tool calls, costs. */

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function CallDetailPage({ params }: { params: { id: string } }) {
  let detail: Awaited<ReturnType<typeof api.getCall>> | null = null;
  let error: string | null = null;
  try {
    detail = await api.getCall(params.id);
  } catch (e) {
    error = e instanceof Error ? e.message : "unknown error";
  }

  if (error || !detail) {
    return (
      <div className="p-6">
        <p className="text-sm text-destructive">Failed to load call: {error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">
            Call from {detail.started_at ? new Date(detail.started_at).toLocaleString() : "—"}
          </h1>
          <p className="text-sm text-muted-foreground">
            {detail.direction} · {detail.duration_sec ?? "?"}s · ${detail.cost_total_usd.toFixed(4)}
          </p>
        </div>
        {detail.flagged ? <Badge variant="warning">flagged</Badge> : null}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm">{detail.summary ?? "Pending — generated after hangup."}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Transcript</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {detail.turns.length === 0 ? (
              <p className="text-sm text-muted-foreground">No turns yet.</p>
            ) : (
              detail.turns.map((t) => (
                <div
                  key={t.id}
                  className={`rounded p-2 text-sm ${
                    t.role === "caller" ? "bg-muted" : "bg-primary/10"
                  }`}
                >
                  <span className="mr-2 text-xs uppercase text-muted-foreground">
                    {t.role}
                  </span>
                  {t.text ?? t.tool_name ?? "(empty turn)"}
                  {t.latency_ms ? (
                    <span className="ml-2 text-xs text-muted-foreground">
                      {t.latency_ms}ms
                    </span>
                  ) : null}
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recording</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Audio player will appear here once recordings are wired up.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}