// Utilities for computing training load and ACWR (acute:chronic workload ratio)
// Assumptions / notes:
// - Grades are numeric values (e.g., V-scale mapped to numbers). The relative intensity uses a base of 1.4 as in the referenced slides.
// - If a user's max grade (gMax) is not provided, we'll default to the max grade found in the provided sessions (or fallback to the highest grade seen).
// - We compute EWMA across sessions (ordered by date). This treats sessions as a time-series without explicit day gaps; for a more precise time-decay EWMA you'd weight by days between sessions.

export type Climb = {
  name: string;
  grade: number; // numeric grade
  attempts?: number;
  flagBoulder?: boolean;
  flagSport?: boolean;
};

export type TrainingSession = {
  name: string;
  scheduledDate: string; // ISO date string
  description?: string;
  workoutId?: string;
  climbs: Climb[];
};

export const defaultWeights = {
  boulder: 1.0,
  sport: 0.75,
  other: 0.8
};

export function relIntensity(grade: number, gMax: number) {
  // RelIntensity = 1.4^{G_i} / 1.4^{G_max} = 1.4^{(G_i - G_max)}
  if (gMax === undefined || gMax === null) return 1;
  return Math.pow(1.4, grade - gMax);
}

export function parseGrade(value: string | number | undefined | null): number {
  if (value === undefined || value === null) return 0;
  if (typeof value === 'number') return value;
  const s = String(value).trim().toUpperCase();
  // V-scale: V0...V17 -> number after V
  const vMatch = s.match(/^V(\d+)$/i);
  if (vMatch) return parseInt(vMatch[1], 10);
  // YDS: 5.10a, 5.12d -> take the numeric part after 5.
  const yMatch = s.match(/^5\.(\d{1,2})/);
  if (yMatch) return parseInt(yMatch[1], 10);
  // Fallback: parse numeric
  const n = parseFloat(s);
  return Number.isFinite(n) ? n : 0;
}

export function climbLoad(climb: Climb, gMax: number, weights = defaultWeights) {
  const attempts = Math.max(1, climb.attempts ?? 1);
  const intensity = relIntensity(climb.grade, gMax);
  let w = weights.other;
  if (climb.flagBoulder) w = weights.boulder;
  else if (climb.flagSport) w = weights.sport;
  return attempts * intensity * w;
}

export function sessionLoad(session: TrainingSession, gMax: number, weights = defaultWeights) {
  return (session.climbs || []).reduce((sum, c) => sum + climbLoad(c, gMax, weights), 0);
}

export function computeSessionLoads(sessions: TrainingSession[] | any, gMax?: number, weights = defaultWeights) {
  if (!Array.isArray(sessions)) {
    return { sessions: [], gMax: gMax ?? 0 };
  }
  // Normalize climbs: ensure grade is numeric (accept strings like 'V4' or '5.10a')
  const normalized = sessions.map((s: any) => ({
    ...s,
    climbs: (s.climbs || []).map((c: any) => ({ ...c, grade: parseGrade(c.grade) }))
  }));

  // If gMax not provided, infer from sessions
  let inferredGMax = gMax;
  if (inferredGMax === undefined || inferredGMax === null) {
    const allGrades = normalized
      .flatMap((s: any) => (s.climbs || []).map((c: any) => c.grade ?? -Infinity))
      .filter((g: any) => Number.isFinite(g));
    inferredGMax = allGrades.length ? Math.max(...allGrades) : 0;
  }

  const out = normalized
    .slice()
    .sort((a: any, b: any) => new Date(a.scheduledDate).getTime() - new Date(b.scheduledDate).getTime())
    .map((s: any) => ({
      scheduledDate: s.scheduledDate,
      name: s.name,
      load: sessionLoad(s, inferredGMax!, weights)
    }));

  return { sessions: out, gMax: inferredGMax };
}

export function ewma(values: number[], span: number) {
  if (!values || !values.length) return [];
  const alpha = 2 / (span + 1);
  const out: number[] = [];
  let s = values[0];
  out.push(s);
  for (let i = 1; i < values.length; i++) {
    s = alpha * values[i] + (1 - alpha) * s;
    out.push(s);
  }
  return out;
}

export type ACWROptions = {
  timeWeighted?: boolean; // when true, account for days between sessions
  span7?: number; // days for acute window (default 7)
  span42?: number; // days for chronic window (default 42)
};

function dailyAlphaForSpan(spanDays: number) {
  // Base daily alpha such that alpha_for_1day = 2/(span+1)
  return 2 / (spanDays + 1);
}

function combinedAlpha(alphaPerDay: number, deltaDays: number) {
  // Combine per-day alpha over deltaDays: alpha_combined = 1 - (1 - alphaPerDay)^{deltaDays}
  if (deltaDays <= 1) return alphaPerDay;
  return 1 - Math.pow(1 - alphaPerDay, deltaDays);
}

export function computeACWR(sessionLoads: { scheduledDate: string; load: number }[], opts: ACWROptions = {}) {
  const { timeWeighted = false, span7 = 7, span42 = 42 } = opts;
  // sort by date
  const sorted = (sessionLoads || []).slice().sort((a, b) => new Date(a.scheduledDate).getTime() - new Date(b.scheduledDate).getTime());
  const loads = sorted.map(s => s.load ?? 0);
  if (!loads.length) return { ewma7: null, ewma42: null, acwr: null };

  if (!timeWeighted) {
    const ewma7Series = ewma(loads, span7);
    const ewma42Series = ewma(loads, span42);
    const ewma7 = ewma7Series[ewma7Series.length - 1];
    const ewma42 = ewma42Series[ewma42Series.length - 1];
    const acwr = ewma42 && ewma42 > 0 ? ewma7 / ewma42 : null;
    return { ewma7, ewma42, acwr, ewma7Series, ewma42Series } as any;
  }

  // time-weighted EWMA: compute per-session using days between sessions
  const ewma7Series: number[] = [];
  const ewma42Series: number[] = [];
  const alpha7PerDay = dailyAlphaForSpan(span7);
  const alpha42PerDay = dailyAlphaForSpan(span42);

  let lastDate = new Date(sorted[0].scheduledDate);
  let s7 = loads[0];
  let s42 = loads[0];
  ewma7Series.push(s7);
  ewma42Series.push(s42);

  for (let i = 1; i < sorted.length; i++) {
    const d = new Date(sorted[i].scheduledDate);
    const deltaDays = Math.max(1, Math.round((d.getTime() - lastDate.getTime()) / (1000 * 60 * 60 * 24)));
    const a7 = combinedAlpha(alpha7PerDay, deltaDays);
    const a42 = combinedAlpha(alpha42PerDay, deltaDays);
    s7 = a7 * loads[i] + (1 - a7) * s7;
    s42 = a42 * loads[i] + (1 - a42) * s42;
    ewma7Series.push(s7);
    ewma42Series.push(s42);
    lastDate = d;
  }

  const ewma7 = ewma7Series[ewma7Series.length - 1];
  const ewma42 = ewma42Series[ewma42Series.length - 1];
  const acwr = ewma42 && ewma42 > 0 ? ewma7 / ewma42 : null;
  return { ewma7, ewma42, acwr, ewma7Series, ewma42Series } as any;
}

export default {
  relIntensity,
  climbLoad,
  sessionLoad,
  computeSessionLoads,
  computeACWR,
  ewma,
};
