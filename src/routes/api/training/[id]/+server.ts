import type { RequestHandler } from './$types';
import { json, error } from '@sveltejs/kit';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export const GET: RequestHandler = async ({ params }) => {
  const id = params.id;

  const session = await prisma.trainingSession.findUnique({
    where: { id },
    include: {
      workout: {
        include: {
          exercises: { orderBy: { orderIdx: 'asc' } }
        }
      },
      climbs: { orderBy: { name: 'asc' } }
    }
  });

  if (!session) throw error(404, 'Training session not found');
  return json(session);
};
