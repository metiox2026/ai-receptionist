/** Messages inbox — staff assign, add notes, mark done. */

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

const STATUS_VARIANT = {
  new: "destructive",
  in_progress: "warning",
  done: "success",
} as const;

export default async function MessagesPage() {
  let messages: Awaited<ReturnType<typeof api.listMessages>> = [];
  let error: string | null = null;
  try {
    messages = await api.listMessages();
  } catch (e) {
    error = e instanceof Error ? e.message : "unknown error";
  }

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-3xl font-semibold tracking-tight">Messages</h1>

      {error ? (
        <p className="text-sm text-destructive">Failed to load messages: {error}</p>
      ) : messages.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            No messages yet. Messages taken by the agent will appear here.
          </CardContent>
        </Card>
      ) : (
        <div className="overflow-hidden rounded-lg border">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/50 text-left">
              <tr>
                <th className="px-4 py-2 font-medium">When</th>
                <th className="px-4 py-2 font-medium">Caller</th>
                <th className="px-4 py-2 font-medium">Phone</th>
                <th className="px-4 py-2 font-medium">Reason</th>
                <th className="px-4 py-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {messages.map((m) => (
                <tr key={m.id} className="border-b hover:bg-muted/30">
                  <td className="px-4 py-2">{new Date(m.created_at).toLocaleString()}</td>
                  <td className="px-4 py-2">{m.caller_name ?? "—"}</td>
                  <td className="px-4 py-2">{m.caller_phone ?? "—"}</td>
                  <td className="px-4 py-2">{m.reason ?? "—"}</td>
                  <td className="px-4 py-2">
                    <Badge variant={STATUS_VARIANT[m.status]}>{m.status}</Badge>
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