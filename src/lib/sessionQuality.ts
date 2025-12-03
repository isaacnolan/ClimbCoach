// src/lib/sessionQuality.ts

// ===== Types =====

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
    progressScore: number;    // 0–20 (near-PR sessions)
  
    // final 0–100
    score: number;
  };
  
  // Aggregated stats across a set of sessions (e.g. selected subset in the UI)
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
  
  // ===== Single-session computation =====
  
  // Compute a single session's breakdown given the global max grade
  function computeSessionQualitySingle(
    session: TrainingSessionForQuality,
    globalMaxGrade: number
  ): SessionQualityBreakdown {
    // ----- Climb metrics -----
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
  
    // ----- Workout / exercise metrics -----
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
  
    // Simple "training load" heuristic:
    // - each climb has its own volume weight
    // - each exercise set and each minute of exercise also contribute to volume
    const climbVolumeUnits = totalClimbs * 3 + totalAttempts * 0.5;
    const exerciseVolumeUnits =
      totalExerciseSets * 1.5 + totalExerciseMinutes * 1.0;
  
    const totalTrainingLoad = climbVolumeUnits + exerciseVolumeUnits;
  
    const safeGlobalMax = globalMaxGrade > 0 ? globalMaxGrade : 1;
  
    // ----- component scores -----
  
    // 1) Volume: more climbs + more exercises = higher, cap at 20
    //   - climbVolumeUnits already favors more climbs/attempts
    //   - exerciseVolumeUnits adds strength/conditioning volume
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
  
    // 5) Progress: reward sessions with climbs near global max
    let progressScore = 0;
    if (maxGrade != null) {
      const rel = maxGrade / safeGlobalMax;
      if (rel >= 0.98) {
        progressScore = 20; // new peak / matches top
      } else if (rel >= 0.9) {
        progressScore = 14;
      } else if (rel >= 0.8) {
        progressScore = 8;
      } else if (rel >= 0.7) {
        progressScore = 4;
      } else {
        progressScore = 0;
      }
    }
  
    const score =
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
  
      score: clamp(score, 0, 100),
    };
  }
  
  // ===== Multi-session computation =====
  
  // Compute per-session breakdowns + aggregated metrics for ANY subset of sessions
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
  
    // Find global max grade over all climbs in these sessions
    const allGrades: number[] = [];
    for (const s of sessions) {
      for (const c of s.climbs ?? []) {
        if (typeof c.grade === 'number') allGrades.push(c.grade);
      }
    }
    const globalMaxGrade = allGrades.length
      ? Math.max(...allGrades)
      : 0;
  
    const perSession = sessions.map((s) =>
      computeSessionQualitySingle(s, globalMaxGrade)
    );
  
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
  