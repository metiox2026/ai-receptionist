/** Contacts — search, tag, block. */

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ContactsPage() {
  let contacts: Awaited<ReturnType<typeof api.listContacts>> = [];
  let error: string | null = null;
  try {
    contacts = await api.listContacts();
  } catch (e) {
    error = e instanceof Error ? e.message : "unknown error";
  }

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-3xl font-semibold tracking-tight">Contacts</h1>

      {error ? (
        <p className="text-sm text-destructive">Failed to load: {error}</p>
      ) : contacts.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            No contacts yet.
          </CardContent>
        </Card>
      ) : (
        <div className="overflow-hidden rounded-lg border">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/50 text-left">
              <tr>
                <th className="px-4 py-2 font-medium">Name</th>
                <th className="px-4 py-2 font-medium">Phone</th>
                <th className="px-4 py-2 font-medium">Tags</th>
                <th className="px-4 py-2 font-medium">Blocked</th>
              </tr>
            </thead>
            <tbody>
              {contacts.map((c) => (
                <tr key={c.id} className="border-b hover:bg-muted/30">
                  <td className="px-4 py-2">{c.name ?? "—"}</td>
                  <td className="px-4 py-2">{c.phone}</td>
                  <td className="px-4 py-2">
                    {c.tags.length === 0
                      ? "—"
                      : c.tags.map((t) => (
                          <Badge key={t} variant="secondary" className="mr-1">
                            {t}
                          </Badge>
                        ))}
                  </td>
                  <td className="px-4 py-2">
                    {c.is_blocked ? <Badge variant="destructive">blocked</Badge> : null}
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