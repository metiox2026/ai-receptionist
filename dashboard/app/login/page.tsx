/** Login — minimal email/password. NextAuth wires in here. */

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/40 p-6">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Sign in</CardTitle>
          <CardDescription>to the receptionist dashboard</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4">
            <div className="space-y-1">
              <label className="text-sm font-medium" htmlFor="email">
                Email
              </label>
              <Input id="email" name="email" type="email" required />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium" htmlFor="password">
                Password
              </label>
              <Input id="password" name="password" type="password" required />
            </div>
            <Button type="submit" className="w-full">
              Sign in
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}