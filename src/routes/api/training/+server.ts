import type { RequestHandler } from './$types';
import { createTrainingSession, listTrainingSessions } from '$lib/server/training';

export const POST: RequestHandler = async ({ request }) => {
  try {
    const body = await request.json();
    const created = await createTrainingSession(body);
    return new Response(JSON.stringify(created), { status: 201 });
  } catch (e: any) {
    return new Response(JSON.stringify({ error: e?.message || 'Bad Request' }), { status: 400 });
  }
};

export const GET: RequestHandler = async ({ url }) => {
  try {
    const workoutId = url.searchParams.get('workoutId') ?? undefined;
    const from = url.searchParams.get('from') ? new Date(String(url.searchParams.get('from'))) : undefined;
    const to = url.searchParams.get('to') ? new Date(String(url.searchParams.get('to'))) : undefined;
    const cursor = url.searchParams.get('cursor') ?? undefined;
    const take = url.searchParams.get('take') ? Number(url.searchParams.get('take')) : undefined;

    const sessions = await listTrainingSessions({ workoutId, from, to, cursor, take });
    return new Response(JSON.stringify(sessions), { status: 200 });
  } catch (e: any) {
    return new Response(JSON.stringify({ error: e?.message || 'Server error' }), { status: 500 });
  }
};
