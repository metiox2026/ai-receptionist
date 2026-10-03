/** Appointments — calendar + list view. */

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

const STATUS_VARIANT = {
  booked: "default",
  cancelled: "destructive",
  completed: "success",
  no_show: "warning",
} as const;

export default async function AppointmentsPage() {
  let appointments: Awaited<ReturnType<typeof api.listAppointments>> = [];
  let error: string | null = null;
  try {
    appointments = await api.listAppointments();
  } catch (e) {
    error = e instanceof Error ? e.message : "unknown error";
  }

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-3xl font-semibold tracking-tight">Appointments</h1>

      {error ? (
        <p className="text-sm text-destructive">Failed to load: {error}</p>
      ) : appointments.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            No appointments scheduled yet.
          </CardContent>
        </Card>
      ) : (
        <div className="overflow-hidden rounded-lg border">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/50 text-left">
              <tr>
                <th className="px-4 py-2 font-medium">When</th>
                <th className="px-4 py-2 font-medium">Service</th>
                <th className="px-4 py-2 font-medium">Status</th>
                <th className="px-4 py-2 font-medium">Created by</th>
              </tr>
            </thead>
            <tbody>
              {appointments.map((a) => (
                <tr key={a.id} className="border-b hover:bg-muted/30">
                  <td className="px-4 py-2">{new Date(a.starts_at).toLocaleString()}</td>
                  <td className="px-4 py-2">{a.service}</td>
                  <td className="px-4 py-2">
                    <Badge variant={STATUS_VARIANT[a.status]}>{a.status}</Badge>
                  </td>
                  <td className="px-4 py-2">{a.created_by}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}