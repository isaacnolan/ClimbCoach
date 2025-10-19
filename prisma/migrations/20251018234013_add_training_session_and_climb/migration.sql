-- CreateTable
CREATE TABLE "public"."TrainingSession" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "scheduledDate" TIMESTAMP(3) NOT NULL,
    "description" TEXT NOT NULL,
    "workoutId" TEXT NOT NULL,

    CONSTRAINT "TrainingSession_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."Climb" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "grade" INTEGER NOT NULL,
    "flagBoulder" BOOLEAN NOT NULL DEFAULT false,
    "flagSport" BOOLEAN NOT NULL DEFAULT false,
    "attempts" INTEGER NOT NULL DEFAULT 0,
    "trainingSessionId" TEXT NOT NULL,

    CONSTRAINT "Climb_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "TrainingSession_workoutId_idx" ON "public"."TrainingSession"("workoutId");

-- CreateIndex
CREATE INDEX "Climb_trainingSessionId_idx" ON "public"."Climb"("trainingSessionId");

-- AddForeignKey
ALTER TABLE "public"."TrainingSession" ADD CONSTRAINT "TrainingSession_workoutId_fkey" FOREIGN KEY ("workoutId") REFERENCES "public"."Workout"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."Climb" ADD CONSTRAINT "Climb_trainingSessionId_fkey" FOREIGN KEY ("trainingSessionId") REFERENCES "public"."TrainingSession"("id") ON DELETE CASCADE ON UPDATE CASCADE;
