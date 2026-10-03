/** Agent config — edit persona, business facts, prompt versions, voice. */

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ConfigPage() {
  let versions: Awaited<ReturnType<typeof api.listPromptVersions>> = [];
  let error: string | null = null;
  try {
    versions = await api.listPromptVersions();
  } catch (e) {
    error = e instanceof Error ? e.message : "unknown error";
  }

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-3xl font-semibold tracking-tight">Agent configuration</h1>

      <Card>
        <CardHeader>
          <CardTitle>Prompt versions</CardTitle>
          <CardDescription>
            Draft changes without affecting live calls. Publish to roll out.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error ? (
            <p className="text-sm text-destructive">Failed to load: {error}</p>
          ) : versions.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No prompt versions yet. Run <code>make seed</code> to create the
              initial draft.
            </p>
          ) : (
            <div className="overflow-hidden rounded-lg border">
              <table className="w-full text-sm">
                <thead className="border-b bg-muted/50 text-left">
                  <tr>
                    <th className="px-4 py-2 font-medium">When</th>
                    <th className="px-4 py-2 font-medium">Status</th>
                    <th className="px-4 py-2 font-medium">Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {versions.map((v) => (
                    <tr key={v.id} className="border-b hover:bg-muted/30">
                      <td className="px-4 py-2">{new Date(v.created_at).toLocaleString()}</td>
                      <td className="px-4 py-2">
                        <Badge
                          variant={
                            v.status === "live"
                              ? "success"
                              : v.status === "archived"
                                ? "secondary"
                                : "default"
                          }
                        >
                          {v.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-2 text-muted-foreground">{v.notes ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Business facts, voice & announcements</CardTitle>
          <CardDescription>
            Editors for hours, services, prices, FAQs, voice and announcements.
            Wires up once the prompt editor (Phase 3) is in place.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Form components go here.
        </CardContent>
      </Card>
    </div>
  );
}