# Workout Scheduled Date Feature - Implementation Summary

## Overview
Added support for scheduling workouts by allowing the LLM to include a `scheduledDate` when creating workouts.

## Changes Made

### 1. **API Endpoint** (`src/routes/api/workouts/+server.ts`)
- Added `scheduledDate` parsing in the POST handler
- Validates date format (ISO 8601)
- Returns 400 error if invalid date format is provided
- Passes `scheduledDate` to the database creation function

### 2. **Database Function** (`src/lib/server/db.ts`)
- Added `scheduledDate?: Date` parameter to `createWorkout` function
- Passes `scheduledDate` to Prisma create operation
- Field is optional (can be `undefined`)

### 3. **Claude Agent** (`backend/claude_agent_flow.py`)
- Enhanced LLM prompt to parse and include `scheduledDate` in workout JSON
- Added date parsing rules for the LLM:
  - Specific dates: "October 10, 2025", "2025-10-15"
  - Relative dates: "tomorrow", "next Monday"
  - No date: Sets `scheduledDate` to `null`
- Includes current date context (October 9, 2025) for relative date calculations
- Outputs ISO 8601 format for consistency

### 4. **Test Script** (`backend/test_workout_creation.py`)
- Updated examples to include workouts with scheduled dates
- Added examples with:
  - Specific dates
  - Relative dates ("tomorrow", "next Monday")
  - No dates

### 5. **Documentation** (`backend/WORKOUT_CREATION_README.md`)
- Added `scheduledDate` to API schema documentation
- Included date format examples
- Added date parsing support section
- Updated usage examples with date scheduling
- Marked "Schedule workouts" enhancement as completed

## Usage Examples

### With Specific Date
```python
coach = ClimbingCoachSystem()
response = coach.create_training_plan(
    "Create a workout called 'Power Training' scheduled for October 15, 2025 "
    "with campus board: 4 sets of 6 rungs with 3 minute rest"
)
```

### With Relative Date
```python
response = coach.create_training_plan(
    "Create a workout for tomorrow called 'Quick Session' with hangboard: 3 sets of 10 seconds"
)
```

### Without Date (date will be null)
```python
response = coach.create_training_plan(
    "Create a workout called 'Unscheduled Training' with core work: 3 sets of 45 seconds"
)
```

## JSON Structure

The LLM now generates workout JSON with the optional `scheduledDate` field:

```json
{
  "name": "Power Training",
  "description": "Campus board power session",
  "userId": null,
  "scheduledDate": "2025-10-15T00:00:00.000Z",
  "exercises": [
    {
      "name": "Campus Board Ladders",
      "sets": 4,
      "reps": 6,
      "duration": null,
      "rest": 180
    }
  ]
}
```

## Date Formats Supported

The LLM can understand and parse:
- **Specific dates**: "October 10, 2025", "2025-10-15", "Oct 10"
- **Relative dates**: "tomorrow", "next Monday", "in 3 days", "next week"
- **No date**: If not mentioned, `scheduledDate` is set to `null`

All dates are converted to ISO 8601 format with UTC timezone.

## Database Schema

The Prisma schema already had the `scheduledDate` field:

```prisma
model Workout {
  id            String     @id @default(cuid())
  userId        String?
  name          String
  description   String?
  createdAt     DateTime   @default(now())
  scheduledDate DateTime?  // ✅ Already existed in schema
  exercises     Exercise[]
  Progress      Progress[]
}
```

## Testing

Run the test script to see date scheduling in action:

```bash
cd backend
python test_workout_creation.py
```

The test includes examples with:
1. Specific date (October 10, 2025)
2. Relative date (tomorrow)
3. Relative date (next Monday)
4. No date specified

## Benefits

1. **Natural Language**: Users can specify dates in natural language
2. **Flexible**: Supports specific dates, relative dates, or no date
3. **Validated**: API validates date format before saving
4. **Consistent**: All dates stored in ISO 8601 format
5. **Calendar Ready**: Workouts can now be displayed on a calendar view

## Next Steps

Potential enhancements:
- Add timezone support (currently uses UTC)
- Support recurring workouts (e.g., "every Monday")
- Add date range queries for fetching workouts
- Calendar view integration in the frontend
- Workout reminders/notifications based on scheduled date
