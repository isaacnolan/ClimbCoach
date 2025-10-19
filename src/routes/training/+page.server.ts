import type { PageServerLoad } from './$types';
import { prisma } from '$lib/server/db';

export const load: PageServerLoad = async () => {
  const sessions = await prisma.trainingSession.findMany({
    include: { workout: true, climbs: true },
    orderBy: { scheduledDate: 'desc' }
  });
  return { sessions };
};
