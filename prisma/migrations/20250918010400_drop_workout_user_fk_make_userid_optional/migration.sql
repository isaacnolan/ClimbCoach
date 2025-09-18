/*
  Warnings:

  - You are about to drop the column `createdAt` on the `User` table. All the data in the column will be lost.
  - You are about to drop the column `updatedAt` on the `Workout` table. All the data in the column will be lost.
  - Made the column `email` on table `User` required. This step will fail if there are existing NULL values in that column.

*/
-- DropForeignKey
ALTER TABLE "public"."Workout" DROP CONSTRAINT "Workout_userId_fkey";

-- DropIndex
DROP INDEX "public"."Workout_userId_idx";

-- AlterTable
ALTER TABLE "public"."User" DROP COLUMN "createdAt",
ALTER COLUMN "email" SET NOT NULL;

-- AlterTable
ALTER TABLE "public"."Workout" DROP COLUMN "updatedAt",
ALTER COLUMN "userId" DROP NOT NULL;
