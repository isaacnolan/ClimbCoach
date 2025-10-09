// src/routes/api/workouts/+server.ts
import type { RequestHandler } from './$types';
import { createWorkout as dbCreate, getWorkouts as dbList } from '$lib/server/db';

// Create workout
export const POST: RequestHandler = async ({ request }) => {
  try {
    const b = await request.json();

    if (!b?.name?.trim()) {
      return new Response(JSON.stringify({ error: 'name is required' }), { status: 400 });
    }

    // Parse scheduledDate if provided
    let scheduledDate: Date | undefined = undefined;
    if (b.scheduledDate) {
      scheduledDate = new Date(b.scheduledDate);
      // Validate the date
      if (isNaN(scheduledDate.getTime())) {
        return new Response(JSON.stringify({ error: 'Invalid scheduledDate format' }), { status: 400 });
      }
    }

    const created = await dbCreate({
      name: b.name.trim(),
      description: b.description ?? undefined,
      userId: b.userId ?? null, // optional
      scheduledDate: scheduledDate,
      exercises: (b.exercises ?? []).map((e: any) => ({
        name: e.name,
        sets: Number(e.sets) || 0,
        reps: e.reps ?? undefined,
        duration: e.duration ?? undefined,
        rest: e.rest ?? undefined,
      })),
    });

    return new Response(JSON.stringify(created), { status: 201 });
  } catch (err: any) {
    console.error('POST /api/workouts failed:', err);
    return new Response(JSON.stringify({ error: err?.message || 'Server error' }), { status: 500 });
  }
};

// List workouts (optionally by userId; we won’t filter on UI right now)
export const GET: RequestHandler = async ({ url }) => {
  try {
    const userId = url.searchParams.get('userId') || undefined;
    const workouts = await dbList(userId || undefined);
    return new Response(JSON.stringify(workouts), { status: 200 });
  } catch (err: any) {
    console.error('GET /api/workouts failed:', err);
    return new Response(JSON.stringify({ error: err?.message || 'Server error' }), { status: 500 });
  }
};
