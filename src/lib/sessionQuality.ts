
// Individual climb inside a training session
export type ClimbInSession = {
  id: string;
  grade?: number | null;
  attempts?: number | null;
  completed?: boolean | null;
};

// Exercise inside the associated workout
export type WorkoutExercise = {
  id: string;
  name: string;
  sets?: number | null;
  reps?: number | null;
  duration?: number | null; // seconds (as in your Exercise UI)
};

// Workout attached to a training session
export type WorkoutForQuality = {
  id: string;
  name: string | null;
  exercises?: WorkoutExercise[]; // optional – safe if backend doesn't send them yet
};

// Training session used for quality calculation
export type TrainingSessionForQuality = {
  id: string;
  name: string;
  scheduledDate: string; // ISO string
  description: string | null;
  workout: WorkoutForQuality | null;
  climbs: ClimbInSession[];
};

// Per-session breakdown of quality
export type SessionQualityBreakdown = {
  sessionId: string;
  name: string;
  scheduledDate: string;
  workoutName: string | null;

  // basic climb metrics
  totalClimbs: number;
  totalAttempts: number;
  avgGrade: number | null;
  maxGrade: number | null;
  avgAttemptsPerClimb: number | null;

  // basic workout / exercise metrics
  totalExerciseSets: number;
  totalExerciseMinutes: number;
  // combined "load" units used internally for volume
  totalTrainingLoad: number;

  // component scores
  volumeScore: number;      // 0–20 (climbs + exercises)
  difficultyScore: number;  // 0–25 (mostly climbs)
  consistencyScore: number; // 0–20 (attempts/climb)
  intensityScore: number;   // 0–15 (hardest grade)
  progressScore: number;    // 0–20 (near-PR sessions, with novelty)

  // final 0–100
  score: number;
};

export type AggregatedQuality = {
  sessionsCount: number;
  averageScore: number | null;

  avgVolumeScore: number;
  avgDifficultyScore: number;
  avgConsistencyScore: number;
  avgIntensityScore: number;
  avgProgressScore: number;

  scoreSeries: { date: Date; score: number; name: string }[];
};

function clamp(v: number, min: number, max: number) {
  return Math.max(min, Math.min(max, v));
}

function computeProgressWithNovelty(
  maxGrade: number | null,
  globalMaxGrade: number,
  priorPrHits: number
): { progressScore: number; isPrHit: boolean } {
  if (maxGrade == null || globalMaxGrade <= 0) {
    return { progressScore: 0, isPrHit: false };
  }

  const rel = maxGrade / globalMaxGrade;
  let base = 0;

  if (rel >= 0.98) {
    base = 20;
  } else if (rel >= 0.9) {
    base = 14;
  } else if (rel >= 0.8) {
    base = 8;
  } else if (rel >= 0.7) {
    base = 4;
  } else {
    return { progressScore: 0, isPrHit: false };
  }

  // Only apply novelty decay for true PR-level sessions (rel >= 0.98)
  if (rel >= 0.98) {
    // First time at PR: 100%
    // Next times decay down to a floor (e.g. 40% of base)
    const noveltyFactor = Math.max(0.4, 1 - 0.15 * priorPrHits);
    const score = base * noveltyFactor;
    return { progressScore: score, isPrHit: true };
  }

  return { progressScore: base, isPrHit: false };
}

function computeSessionQualitySingle(
  session: TrainingSessionForQuality,
  globalMaxGrade: number
): SessionQualityBreakdown {
  const climbs = session.climbs ?? [];
  const totalClimbs = climbs.length;

  const grades = climbs
    .map((c) => c.grade)
    .filter((g): g is number => typeof g === 'number');

  const maxGrade = grades.length ? Math.max(...grades) : null;
  const avgGrade = grades.length
    ? grades.reduce((a, b) => a + b, 0) / grades.length
    : null;

  const attemptsArr = climbs.map((c) =>
    typeof c.attempts === 'number' ? c.attempts : 1
  );
  const totalAttempts = attemptsArr.reduce((a, b) => a + b, 0);
  const avgAttemptsPerClimb =
    totalClimbs > 0 ? totalAttempts / totalClimbs : null;

  const exercises = session.workout?.exercises ?? [];
  let totalExerciseSets = 0;
  let totalExerciseSeconds = 0;

  for (const ex of exercises) {
    if (typeof ex.sets === 'number') {
      totalExerciseSets += ex.sets;
    }
    if (typeof ex.duration === 'number') {
      totalExerciseSeconds += ex.duration;
    }
  }

  const totalExerciseMinutes = totalExerciseSeconds / 60;

  const climbVolumeUnits = totalClimbs * 3 + totalAttempts * 0.5;
  const exerciseVolumeUnits =
    totalExerciseSets * 1.5 + totalExerciseMinutes * 1.0;

  const totalTrainingLoad = climbVolumeUnits + exerciseVolumeUnits;

  const safeGlobalMax = globalMaxGrade > 0 ? globalMaxGrade : 1;


  // 1) Volume: more climbs + more exercises = higher, cap at 20
  const volumeScore = clamp(totalTrainingLoad, 0, 20);

  // 2) Difficulty: avg climb grade vs global max, scaled to 25
  const difficultyRatio =
    avgGrade != null ? avgGrade / safeGlobalMax : 0;
  const difficultyScore = clamp(difficultyRatio * 25, 0, 25);

  // 3) Consistency: fewer attempts per climb = better
  let consistencyBase = 0;
  if (avgAttemptsPerClimb != null) {
    // avgAttempts = 1 → good; 3–4 → lower; 5+ → poor
    consistencyBase = clamp(4 - avgAttemptsPerClimb, 0, 4); // 0–4
  }
  const consistencyScore = (consistencyBase / 4) * 20; // 0–20

  // 4) Intensity: emphasize hardest climb vs global max
  const intensityRatio =
    maxGrade != null ? maxGrade / safeGlobalMax : 0;
  const intensityScore = clamp(intensityRatio * 15, 0, 15);

  // ProgressScore will be filled in later using history (novelty).
  const progressScore = 0;

  const baseScore =
    volumeScore +
    difficultyScore +
    consistencyScore +
    intensityScore +
    progressScore;

  return {
    sessionId: session.id,
    name: session.name,
    scheduledDate: session.scheduledDate,
    workoutName: session.workout?.name ?? null,

    totalClimbs,
    totalAttempts,
    avgGrade,
    maxGrade,
    avgAttemptsPerClimb,

    totalExerciseSets,
    totalExerciseMinutes,
    totalTrainingLoad,

    volumeScore,
    difficultyScore,
    consistencyScore,
    intensityScore,
    progressScore,

    score: clamp(baseScore, 0, 100),
  };
}


export function computeSessionQualities(
  sessions: TrainingSessionForQuality[]
): { perSession: SessionQualityBreakdown[]; aggregated: AggregatedQuality } {
  if (!sessions.length) {
    return {
      perSession: [],
      aggregated: {
        sessionsCount: 0,
        averageScore: null,
        avgVolumeScore: 0,
        avgDifficultyScore: 0,
        avgConsistencyScore: 0,
        avgIntensityScore: 0,
        avgProgressScore: 0,
        scoreSeries: [],
      },
    };
  }

  const allGrades: number[] = [];
  for (const s of sessions) {
    for (const c of s.climbs ?? []) {
      if (typeof c.grade === 'number') allGrades.push(c.grade);
    }
  }
  const globalMaxGrade = allGrades.length
    ? Math.max(...allGrades)
    : 0;

  // First pass: compute base metrics for each session
  const perSession: SessionQualityBreakdown[] = sessions.map((s) =>
    computeSessionQualitySingle(s, globalMaxGrade)
  );

  // Second pass: compute progressScore with novelty based on history
  // We need to know "how many PR-level sessions have happened BEFORE this one"
  // so we sort by date and walk forward in time.
  const indexed = perSession
    .map((s, idx) => ({
      idx,
      session: s,
      date: new Date(s.scheduledDate),
    }))
    .sort((a, b) => a.date.getTime() - b.date.getTime());

  let priorPrHits = 0;

  for (const { idx, session } of indexed) {
    const { progressScore, isPrHit } = computeProgressWithNovelty(
      session.maxGrade,
      globalMaxGrade,
      priorPrHits
    );

    perSession[idx].progressScore = progressScore;

    const newScore =
      perSession[idx].volumeScore +
      perSession[idx].difficultyScore +
      perSession[idx].consistencyScore +
      perSession[idx].intensityScore +
      perSession[idx].progressScore;

    perSession[idx].score = clamp(newScore, 0, 100);

    if (isPrHit) {
      priorPrHits += 1;
    }
  }

  const n = perSession.length;
  const sum = (fn: (x: SessionQualityBreakdown) => number) =>
    perSession.reduce((acc, s) => acc + fn(s), 0);

  const avgScore = sum((s) => s.score) / n;

  const aggregated: AggregatedQuality = {
    sessionsCount: n,
    averageScore: avgScore || null,
    avgVolumeScore: sum((s) => s.volumeScore) / n,
    avgDifficultyScore: sum((s) => s.difficultyScore) / n,
    avgConsistencyScore: sum((s) => s.consistencyScore) / n,
    avgIntensityScore: sum((s) => s.intensityScore) / n,
    avgProgressScore: sum((s) => s.progressScore) / n,
    scoreSeries: perSession
      .map((s) => ({
        date: new Date(s.scheduledDate),
        score: s.score,
        name: s.name,
      }))
      .sort((a, b) => a.date.getTime() - b.date.getTime()),
  };

  return { perSession, aggregated };
}

// Friendly label for a score
export function qualityRating(score: number | null | undefined): string {
  if (score == null) return 'N/A';
  if (score >= 85) return 'Elite Session';
  if (score >= 70) return 'Strong Session';
  if (score >= 50) return 'Solid Session';
  if (score >= 30) return 'Light Session';
  return 'Recovery / Easy';
}
