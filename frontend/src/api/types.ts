export type Role = "business" | "student";
export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
}
export interface Brief {
  title: string;
  problem: string;
  goal: string;
  deliverable: string;
  success_criteria: string;
  target_users: string;
  constraints: string;
  timeline: string;
  resources: string;
  risk_context: string;
}
export type BriefField = keyof Brief;
export interface Assessment {
  total: number;
  level: string;
  source: string;
  warning: string | null;
  missing_fields: string[];
  next_questions: { field: BriefField; question: string }[];
  scores: Record<string, { score: number; maximum: number; reason: string }>;
}
export interface Task {
  id: string;
  business_id?: string;
  raw_text?: string;
  brief: Brief;
  skill_slugs: string[];
  status: "draft" | "published" | "team_selected";
  quality_score: number;
  quality_level: string;
  assessment?: Assessment | null;
  revision?: number;
  created_at: string;
  published_at: string | null;
}
export interface Team {
  id: string;
  name: string;
  description: string;
  skill_slugs: string[];
  member_ids: string[];
}
export interface TeamDetail extends Team {
  open_to_join: boolean;
  owner_id: string;
  members: { id: string; name: string }[];
}
export interface Proposal {
  id: string;
  task_id: string;
  team_id: string;
  pitch: string;
  approach: string;
  timeline: string;
  status: "submitted" | "selected" | "rejected";
  created_at: string;
}
export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}
export interface Skill {
  slug: string;
  name: string;
}
export const labels: Record<BriefField, string> = {
  title: "Название задачи",
  problem: "Проблема бизнеса",
  goal: "Цель проекта",
  deliverable: "Ожидаемый результат",
  success_criteria: "Критерии успеха",
  target_users: "Целевая аудитория",
  constraints: "Ограничения",
  timeline: "Срок и объём работы",
  resources: "Данные и ресурсы",
  risk_context: "Риски и безопасность",
};
export const statusLabels = {
  draft: "Черновик",
  published: "Открыта для команд",
  team_selected: "Команда выбрана",
  submitted: "На рассмотрении",
  selected: "Выбрана",
  rejected: "Выбрана другая команда",
};
