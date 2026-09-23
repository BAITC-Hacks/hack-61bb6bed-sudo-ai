import { post } from "./client";
import type { BriefField } from "./types";
export type InterviewPlan = {
  summary: string;
  questions: { field: BriefField; question: string; hint: string }[];
  source: string;
  warning: string | null;
};
export type CoachReply = {
  question: string;
  hint: string;
  suggestion: string;
  followups: string[];
  source: string;
  warning: string | null;
  revision: number;
  field: BriefField;
};
// React StrictMode may mount twice; share only requests currently in flight.
const pending = new Map<string, Promise<unknown>>();
export function interviewRequest<T>(path: string, body?: unknown): Promise<T> {
  const key = path + JSON.stringify(body ?? null);
  if (pending.has(key)) return pending.get(key) as Promise<T>;
  const promise = post<T>(path, body).finally(() => pending.delete(key));
  pending.set(key, promise);
  return promise;
}
