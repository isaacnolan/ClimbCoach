import { PrismaClient } from '@prisma/client';

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

export const prisma = globalForPrisma.prisma ?? new PrismaClient();

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = prisma;
}

// Helper functions for common operations
export async function createWorkout(data: {
  name: string;
  description?: string;
  userId: string;
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
        userId: data.userId,
        exercises: {
          create: data.exercises,
        },
      },
      include: {
        exercises: true,
      },
    });
  } catch (error) {
    console.error('Database error in createWorkout:', error);
    // Re-throw the error after logging it
    throw new Error('Failed to create workout. Database error.');
  }
}

export async function getWorkouts(userId: string) {
  try {
    return await prisma.workout.findMany({
      where: { userId },
      include: { exercises: true },
      orderBy: { createdAt: 'desc' },
    });
  } catch (error) {
    console.error('Database error in getWorkouts:', error);
    // Return empty array instead of throwing error
    return [];
  }
}

export async function recordProgress(data: {
  userId: string;
  maxGrade?: string;
  notes?: string;
}) {
  try {
    return await prisma.progress.create({
      data: {
        userId: data.userId,
        maxGrade: data.maxGrade,
        notes: data.notes,
      },
    });
  } catch (error) {
    console.error('Database error in recordProgress:', error);
    throw new Error('Failed to record progress. Database error.');
  }
}

export async function getProgress(userId: string) {
  try {
    return await prisma.progress.findMany({
      where: { userId },
      orderBy: { date: 'desc' },
    });
  } catch (error) {
    console.error('Database error in getProgress:', error);
    // Return empty array instead of throwing error
    return [];
  }
} 