/** Types matching api/schemas.py. Keep in sync when adding fields. */

export type CallDirection = "inbound" | "outbound";
export type MessageStatus = "new" | "in_progress" | "done";
export type AppointmentStatus = "booked" | "cancelled" | "completed" | "no_show";
export type PromptStatus = "draft" | "live" | "archived";

export interface Business {
  id: string;
  name: string;
  timezone: string;
  phone_number: string | null;
}

export interface Contact {
  id: string;
  phone: string;
  name: string | null;
  tags: string[];
  is_blocked: boolean;
}

export interface CallTurn {
  id: number;
  turn_index: number;
  role: "caller" | "agent" | "tool";
  text: string | null;
  tool_name: string | null;
  latency_ms: number | null;
}

export interface Call {
  id: string;
  provider_call_id: string | null;
  direction: CallDirection;
  started_at: string | null;
  ended_at: string | null;
  duration_sec: number | null;
  language: string | null;
  intent: string | null;
  outcome: string | null;
  summary: string | null;
  flagged: boolean;
}

export interface CallDetail extends Call {
  turns: CallTurn[];
  cost_total_usd: number;
}

export interface Message {
  id: string;
  caller_name: string | null;
  caller_phone: string | null;
  reason: string | null;
  status: MessageStatus;
  created_at: string;
}

export interface Appointment {
  id: string;
  service: string;
  starts_at: string;
  ends_at: string;
  status: AppointmentStatus;
  created_by: "ai" | "staff";
}

export interface PromptVersion {
  id: string;
  status: PromptStatus;
  notes: string | null;
  created_at: string;
}

export interface KnowledgeItem {
  id: string;
  title: string;
  updated_at: string;
}

export interface KnowledgeGap {
  id: string;
  question: string;
  status: string;
  created_at: string;
}

export interface OverviewStats {
  calls_today: number;
  answer_rate: number;
  avg_duration_sec: number;
  bookings_today: number;
  messages_today: number;
  transfers_today: number;
  cost_today_usd: number;
  cost_mtd_usd: number;
  active_calls: number;
  agent_healthy: boolean;
}