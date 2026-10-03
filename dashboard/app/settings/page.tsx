/** Settings — users, notification channels, API keys, retention, audit log. */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function SettingsPage() {
  return (
    <div className="space-y-6 p-6">
      <h1 className="text-3xl font-semibold tracking-tight">Settings</h1>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Users and roles</CardTitle>
            <CardDescription>owner, manager, staff, read-only</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Invite + role-management UI goes here. Backed by /auth/signup and
            the users table.
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Notification channels</CardTitle>
            <CardDescription>Telegram, email, Slack</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Channel configuration form goes here. API keys and chat ids are
            encrypted at rest.
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>API keys and integrations</CardTitle>
            <CardDescription>Telnyx, Deepgram, TTS, calendar</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Secrets live in .env, not in the database. Use this page to rotate
            shared keys (Google OAuth refresh token, etc.).
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Retention & privacy</CardTitle>
            <CardDescription>Recording, transcript retention</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Retention window selector + button to purge old data goes here.
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Spending limits</CardTitle>
            <CardDescription>Per-call, daily, monthly</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Caps are enforced in the api service; this page just shows current
            limits and current spend.
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Audit log</CardTitle>
            <CardDescription>Who changed what, when</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Audit log table goes here.
          </CardContent>
        </Card>
      </div>
    </div>
  );
}