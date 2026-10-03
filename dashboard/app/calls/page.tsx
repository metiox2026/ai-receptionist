/** Calls — list view with filters, detail page below. */

import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function CallsPage() {
  let calls: Awaited<ReturnType<typeof api.listCalls>> = [];
  let error: string | null = null;
  try {
    calls = await api.listCalls({ limit: 50 });
  } catch (e) {
    error = e instanceof Error ? e.message : "unknown error";
  }

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-3xl font-semibold tracking-tight">Calls</h1>

      {error ? (
        <p className="text-sm text-destructive">Failed to load calls: {error}</p>
      ) : calls.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            No calls yet. When the agent picks up its first call, it will show
            up here.
          </CardContent>
        </Card>
      ) : (
        <div className="overflow-hidden rounded-lg border">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/50 text-left">
              <tr>
                <th className="px-4 py-2 font-medium">Time</th>
                <th className="px-4 py-2 font-medium">Direction</th>
                <th className="px-4 py-2 font-medium">Duration</th>
                <th className="px-4 py-2 font-medium">Intent</th>
                <th className="px-4 py-2 font-medium">Outcome</th>
                <th className="px-4 py-2 font-medium">Flagged</th>
              </tr>
            </thead>
            <tbody>
              {calls.map((c) => (
                <tr key={c.id} className="border-b hover:bg-muted/30">
                  <td className="px-4 py-2">
                    <Link href={`/calls/${c.id}`} className="hover:underline">
                      {c.started_at ? new Date(c.started_at).toLocaleString() : "—"}
                    </Link>
                  </td>
                  <td className="px-4 py-2">{c.direction}</td>
                  <td className="px-4 py-2">
                    {c.duration_sec ? `${c.duration_sec}s` : "—"}
                  </td>
                  <td className="px-4 py-2">{c.intent ?? "—"}</td>
                  <td className="px-4 py-2">{c.outcome ?? "—"}</td>
                  <td className="px-4 py-2">
                    {c.flagged ? <Badge variant="warning">flagged</Badge> : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}