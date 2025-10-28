import type { RequestHandler } from './$types';
import { prisma } from '$lib/server/db';

export const GET: RequestHandler = async ({ url }) => {
  const lite = url.searchParams.get('lite') === '1';
  const data = await prisma.workout.findMany({
    orderBy: { createdAt: 'desc' },
    select: lite ? { id: true, name: true, description: true } : undefined
  });
  return new Response(JSON.stringify(data), { status: 200 });
};

export const POST: RequestHandler = async ({ request }) => {
  try {
    const body = await request.json();
    if (!body?.name) return new Response(JSON.stringify({ error: 'name required' }), { status: 400 });

    if (!body?.name?.trim()) {
      return new Response(JSON.stringify({ error: 'name is required' }), { status: 400 });
    }

    // Parse scheduledDate if provided
    let scheduledDate: Date | undefined = undefined;
    if (body.scheduledDate) {
      scheduledDate = new Date(body.scheduledDate);
      // Validate the date
      if (isNaN(scheduledDate.getTime())) {
        return new Response(JSON.stringify({ error: 'Invalid scheduledDate format' }), { status: 400 });
      }
    }

    const created = await prisma.workout.create({
      data: {
        name: body.name.trim(),
        description: body.description ?? undefined,
        userId: body.userId ?? null, // optional
        scheduledDate: scheduledDate,
        exercises: (body.exercises ?? []).map((e: any) => ({
          name: e.name,
          sets: Number(e.sets) || 0,
          reps: e.reps ?? undefined,
          duration: e.duration ?? undefined,
          rest: e.rest ?? undefined,
        })),
      },
    });
    return new Response(JSON.stringify(created), { status: 201 });
  } catch (e: any) {
    return new Response(JSON.stringify({ error: e?.message || 'Bad Request' }), { status: 400 });
  }
};
