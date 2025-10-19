import { prisma } from '$lib/server/db';
import { z } from 'zod';

export const ClimbCreate = z.object({
  name: z.string().min(1),
  grade: z.number().int(),
  flagBoulder: z.boolean().optional().default(true),
  flagSport: z.boolean().optional().default(false),
  attempts: z.number().int().nonnegative().optional().default(0),
});

export const ClimbUpdate = z.object({
  name: z.string().min(1).optional(),
  grade: z.number().int().optional(),
  flagBoulder: z.boolean().optional(),
  flagSport: z.boolean().optional(),
  attempts: z.number().int().nonnegative().optional(),
});

export const TrainingCreate = z.object({
  name: z.string().min(1),
  scheduledDate: z.coerce.date(),
  description: z.string().default(''),
  workoutId: z.string().min(1),
  climbs: z.array(ClimbCreate).optional().default([]),
});

export const TrainingUpdate = z.object({
  name: z.string().min(1).optional(),
  scheduledDate: z.coerce.date().optional(),
  description: z.string().optional(),
  workoutId: z.string().min(1).optional(),
});

// ===== TrainingSession CRUD =====
export async function createTrainingSession(input: unknown) {
  const data = TrainingCreate.parse(input);
  const workout = await prisma.workout.findUnique({ where: { id: data.workoutId } });
  if (!workout) throw new Error('Workout not found');

  return prisma.trainingSession.create({
    data: {
      name: data.name,
      description: data.description,
      scheduledDate: data.scheduledDate,
      workoutId: data.workoutId,
      climbs: data.climbs.length ? { create: data.climbs } : undefined,
    },
    include: { climbs: true, workout: true },
  });
}

export async function listTrainingSessions(params?: {
  workoutId?: string;
  from?: Date;
  to?: Date;
  cursor?: string;
  take?: number;
}) {
  const { workoutId, from, to, cursor, take = 20 } = params ?? {};
  return prisma.trainingSession.findMany({
    where: {
      workoutId: workoutId ?? undefined,
      scheduledDate: { gte: from ?? undefined, lte: to ?? undefined },
    },
    include: { climbs: true, workout: true },
    orderBy: { scheduledDate: 'desc' },
    take,
    ...(cursor ? { skip: 1, cursor: { id: cursor } } : {}),
  });
}

export function getTrainingSessionById(id: string) {
  return prisma.trainingSession.findUnique({
    where: { id },
    include: { climbs: true, workout: true },
  });
}

export async function updateTrainingSession(id: string, input: unknown) {
  const data = TrainingUpdate.parse(input);
  if (data.workoutId) {
    const exists = await prisma.workout.findUnique({ where: { id: data.workoutId } });
    if (!exists) throw new Error('New workout not found');
  }
  return prisma.trainingSession.update({
    where: { id },
    data,
    include: { climbs: true, workout: true },
  });
}

export function deleteTrainingSession(id: string) {
  return prisma.trainingSession.delete({ where: { id } });
}

// ===== Climbs (scoped to a session) =====
export async function addClimbToSession(sessionId: string, input: unknown) {
  const data = ClimbCreate.parse(input);
  const session = await prisma.trainingSession.findUnique({ where: { id: sessionId } });
  if (!session) throw new Error('TrainingSession not found');

  return prisma.climb.create({ data: { ...data, trainingSessionId: sessionId } });
}

export function listClimbs(sessionId: string) {
  return prisma.climb.findMany({
    where: { trainingSessionId: sessionId },
    orderBy: { id: 'asc' }, // switch to createdAt if you add timestamps
  });
}

export function updateClimb(climbId: string, input: unknown) {
  const data = ClimbUpdate.parse(input);
  return prisma.climb.update({ where: { id: climbId }, data });
}

export function deleteClimb(climbId: string) {
  return prisma.climb.delete({ where: { id: climbId } });
}

export async function moveClimb(climbId: string, targetSessionId: string) {
  const target = await prisma.trainingSession.findUnique({ where: { id: targetSessionId } });
  if (!target) throw new Error('Target TrainingSession not found');
  return prisma.climb.update({ where: { id: climbId }, data: { trainingSessionId: targetSessionId } });
}
