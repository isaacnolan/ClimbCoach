import type { RequestHandler } from './$types';
import { addClimbToSession, listClimbs } from '$lib/server/training';

export const POST: RequestHandler = async ({ params, request }) => {
  try {
    const body = await request.json();
    const created = await addClimbToSession(params.id, body);
    return new Response(JSON.stringify(created), { status: 201 });
  } catch (e: any) {
    return new Response(JSON.stringify({ error: e?.message || 'Bad Request' }), { status: 400 });
  }
};

export const GET: RequestHandler = async ({ params }) => {
  try {
    const climbs = await listClimbs(params.id);
    return new Response(JSON.stringify(climbs), { status: 200 });
  } catch (e: any) {
    return new Response(JSON.stringify({ error: e?.message || 'Server error' }), { status: 500 });
  }
};
