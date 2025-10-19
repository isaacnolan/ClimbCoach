// src/lib/data/trainingSessions.ts

export type ClimbInput = {
    name: string;
    grade: number;
    attempts?: number;
    flagBoulder?: boolean;
    flagSport?: boolean;
  };
  
  export type TrainingSessionInput = {
    name: string;
    scheduledDate: string; // ISO
    description?: string;
    workoutId: string;
    climbs: ClimbInput[];
  };
  
  export async function getTrainingSessions(params?: {
    from?: string; to?: string; workoutId?: string;
  }) {
    const url = new URL('/api/training', window.location.origin);
    if (params?.from) url.searchParams.set('from', params.from);
    if (params?.to)   url.searchParams.set('to', params.to);
    if (params?.workoutId) url.searchParams.set('workoutId', params.workoutId);
    const res = await fetch(url.toString());
    if (!res.ok) throw new Error('Failed to load training sessions');
    return res.json();
  }
  
  export async function createTrainingSession(payload: TrainingSessionInput) {
    const res = await fetch('/api/training', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const e = await res.json().catch(() => ({}));
      throw new Error(e?.error || 'Failed to create training session');
    }
    return res.json();
  }
  