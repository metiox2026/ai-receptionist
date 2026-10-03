/** Knowledge base — FAQ entries, knowledge gaps list, reindex button. */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function KnowledgePage() {
  let items: Awaited<ReturnType<typeof api.listKnowledge>> = [];
  let gaps: Awaited<ReturnType<typeof api.listKnowledgeGaps>> = [];
  let error: string | null = null;
  try {
    [items, gaps] = await Promise.all([api.listKnowledge(), api.listKnowledgeGaps()]);
  } catch (e) {
    error = e instanceof Error ? e.message : "unknown error";
  }

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-3xl font-semibold tracking-tight">Knowledge base</h1>

      {error && <p className="text-sm text-destructive">Failed to load: {error}</p>}

      <Card>
        <CardHeader>
          <CardTitle>FAQ entries</CardTitle>
          <CardDescription>
            Snippets the agent retrieves with vector search.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {items.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No items yet. Add FAQs and documents here. Embedding index runs
              automatically.
            </p>
          ) : (
            <ul className="divide-y">
              {items.map((it) => (
                <li key={it.id} className="py-2">
                  <div className="font-medium">{it.title}</div>
                  <div className="text-xs text-muted-foreground">
                    updated {new Date(it.updated_at).toLocaleString()}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Knowledge gaps</CardTitle>
          <CardDescription>
            Questions the agent could not answer. Click to add an FAQ so the
            next caller gets the right answer.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {gaps.length === 0 ? (
            <p className="text-sm text-muted-foreground">No gaps yet.</p>
          ) : (
            <ul className="divide-y">
              {gaps.map((g) => (
                <li key={g.id} className="flex items-center justify-between py-2 text-sm">
                  <span>{g.question}</span>
                  <span className="text-xs text-muted-foreground">
                    {new Date(g.created_at).toLocaleString()}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}