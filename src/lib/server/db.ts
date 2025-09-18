// src/lib/server/db.ts
import { PrismaClient } from '@prisma/client';

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient | undefined };
export const prisma = globalForPrisma.prisma ?? new PrismaClient();

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = prisma;
}

export async function createWorkout(data: {
  name: string;
  description?: string;
  userId?: string | null; // optional now
  exercises: {
    name: string;
    description?: string;
    sets: number;
    reps?: number;
    duration?: number;
    rest?: number;
  }[];
}) {
  try {
    return await prisma.workout.create({
      data: {
        name: data.name,
        description: data.description,
        userId: data.userId ?? null,
        exercises: { create: data.exercises },
      },
      include: { exercises: true },
    });
  } catch (error) {
    console.error('Database error in createWorkout:', error);
    throw new Error('Failed to create workout. Database error.');
  }
}

export async function getWorkouts(userId?: string) {
  try {
    return await prisma.workout.findMany({
      where: userId ? { userId } : undefined,
      include: { exercises: true },
      orderBy: { createdAt: 'desc' },
    });
  } catch (error) {
    console.error('Database error in getWorkouts:', error);
    return [];
  }
}
