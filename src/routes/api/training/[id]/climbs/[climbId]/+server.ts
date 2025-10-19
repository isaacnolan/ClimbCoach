import type { RequestHandler } from './$types';
import { updateClimb, deleteClimb, moveClimb } from '$lib/server/training';

export const PATCH: RequestHandler = async ({ params, request }) => {
  try {
    const body = await request.json();
    const updated = await updateClimb(params.climbId, body);
    return new Response(JSON.stringify(updated), { status: 200 });
  } catch (e: any) {
    return new Response(JSON.stringify({ error: e?.message || 'Bad Request' }), { status: 400 });
  }
};

export const DELETE: RequestHandler = async ({ params }) => {
  try {
    await deleteClimb(params.climbId);
    return new Response(null, { status: 204 });
  } catch (e: any) {
    return new Response(JSON.stringify({ error: e?.message || 'Bad Request' }), { status: 400 });
  }
};

// Optional helper: move climb between sessions
export const POST: RequestHandler = async ({ params, request }) => {
  try {
    const { targetSessionId } = await request.json();
    const result = await moveClimb(params.climbId, targetSessionId);
    return new Response(JSON.stringify(result), { status: 200 });
  } catch (e: any) {
    return new Response(JSON.stringify({ error: e?.message || 'Bad Request' }), { status: 400 });
  }
};
