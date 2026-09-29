export type ReviewRole = 'form' | 'visuals' | 'anatomy';

export type ReviewDefect = { phase?: string; view?: string; issue: string; fix?: string };

export type ExerciseReview = {
  score: number;
  confidence: 'low' | 'medium' | 'high';
  summary: string;
  defects: ReviewDefect[];
};

export type ReviewerRecord = {
  role: ReviewRole;
  revision: string;
  reviewedAt: string;
  method: string;
  exercises: Record<string, ExerciseReview>;
};

export type ReviewBundle = { revision: string | null; reviewers: ReviewerRecord[] };

export const ROLE_LABELS: Record<ReviewRole, string> = {
  form: 'Exercise form',
  visuals: 'Visuals',
  anatomy: 'Anatomy',
};
