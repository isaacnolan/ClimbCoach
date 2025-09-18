// src/lib/data/workouts.ts
export async function createWorkout(body: {
  userId?: string;
  name: string;
  description?: string;
  exercises: { name: string; sets: number; reps?: number; duration?: number; rest?: number }[];
}) {
  const res = await fetch('/api/workouts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getWorkouts(userId?: string) {
  const params = new URLSearchParams();
  if (userId) params.set('userId', userId);
  const qs = params.toString();
  const res = await fetch('/api/workouts' + (qs ? `?${qs}` : ''));
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
