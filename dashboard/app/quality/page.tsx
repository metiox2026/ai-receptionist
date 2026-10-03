/** Quality review — random sample queue, flag, regression test results. */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export const dynamic = "force-dynamic";

export default function QualityPage() {
  return (
    <div className="space-y-6 p-6">
      <h1 className="text-3xl font-semibold tracking-tight">Quality review</h1>

      <Card>
        <CardHeader>
          <CardTitle>Random sample</CardTitle>
          <CardDescription>
            Review 10 calls per week. Tag issues so they feed into the
            regression test set.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Queue UI goes here. Each row: thumbs up/down, tag dropdown, "add to
          test set" button.
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Regression test results</CardTitle>
          <CardDescription>
            Latest <code>make eval</code> run. Tool-call accuracy, hallucination
            rate, latency, escalation correctness.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Last run: —. (Wires up once CI uploads results.)
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Prompt version comparison</CardTitle>
          <CardDescription>
            Compare two prompt versions head-to-head on the same calls.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">Coming soon.</CardContent>
      </Card>
    </div>
  );
}