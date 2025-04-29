import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  // Create a test user
  const user = await prisma.user.upsert({
    where: { email: 'test@example.com' },
    update: {},
    create: {
      email: 'test@example.com',
      name: 'Test User',
    },
  });

  // Create sample workouts
  const workouts = [
    {
      name: 'Finger Strength Session',
      description: 'Focus on finger strength and power',
      exercises: [
        {
          name: 'Hangboard Repeaters',
          sets: 3,
          reps: 6,
          duration: 7,
          rest: 3,
        },
        {
          name: 'Max Hangs',
          sets: 4,
          duration: 10,
          rest: 3,
        },
      ],
    },
    {
      name: 'Power Endurance',
      description: 'Build power endurance for bouldering',
      exercises: [
        {
          name: '4x4s',
          sets: 4,
          reps: 4,
          duration: 4,
          rest: 4,
        },
        {
          name: 'Campus Board Ladders',
          sets: 3,
          reps: 5,
          rest: 2,
        },
      ],
    },
    {
      name: 'Technique Drills',
      description: 'Focus on movement and technique',
      exercises: [
        {
          name: 'Silent Feet',
          sets: 3,
          duration: 5,
          rest: 2,
        },
        {
          name: 'Precision Jumps',
          sets: 4,
          reps: 6,
          rest: 2,
        },
      ],
    },
  ];

  // Create workouts and exercises
  for (const workout of workouts) {
    await prisma.workout.create({
      data: {
        name: workout.name,
        description: workout.description,
        userId: user.id,
        exercises: {
          create: workout.exercises,
        },
      },
    });
  }

  // Create some progress entries
  const progressEntries = [
    {
      maxGrade: 'V4',
      notes: 'First V4 send!',
    },
    {
      maxGrade: 'V5',
      notes: 'Project completed after 3 sessions',
    },
  ];

  for (const progress of progressEntries) {
    await prisma.progress.create({
      data: {
        ...progress,
        userId: user.id,
      },
    });
  }

  console.log('Database has been seeded. 🌱');
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  }); 