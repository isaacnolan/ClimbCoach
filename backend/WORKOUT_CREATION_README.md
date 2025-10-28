# Claude Agent Workout Creation Integration

## Overview

The `claude_agent_flow.py` has been enhanced to enable the Claude agent to create workouts and save them directly to your database via the POST API endpoint.

## Changes Made

### 1. **Added HTTP Request Capability**
- Imported `requests` library for making HTTP calls to the backend API
- Added `api_base_url` parameter to the `ClimbingCoachSystem` constructor (default: `http://localhost:5173`)

### 2. **New Method: `create_workout_in_db()`**
This method:
- Takes a natural language workout request from the user
- Uses the LLM to parse it into structured JSON matching your database schema
- POSTs the workout data to `/api/workouts` endpoint
- Returns success/error feedback with the created workout details

**Expected Input Format:**
```
"Create a workout called 'Finger Strength' with hangboard training: 5 sets of 10 seconds with 3 minute rest"
```

**Output JSON Structure (sent to API):**
```json
{
  "name": "Finger Strength",
  "description": "Hangboard training session",
  "userId": null,
  "scheduledDate": "2025-10-10T00:00:00.000Z",
  "exercises": [
    {
      "name": "Hangboard Training",
      "sets": 5,
      "reps": null,
      "duration": 10,
      "rest": 180
    }
  ]
}
```

### 3. **New Agent Tool: `Create_Workout`**
- Registered as a tool available to the coordinator agent
- Allows the agent to recognize workout creation requests
- Automatically routes appropriate requests to the database

### 4. **Enhanced Coordinator Prompt**
- Updated `create_training_plan()` to recognize different types of requests
- Agent can now decide when to create workouts vs. provide advice

## Usage

### Basic Usage

```python
from claude_agent_flow import ClimbingCoachSystem

# Initialize the system
coach = ClimbingCoachSystem()

# Ask the agent to create a workout with a scheduled date
response = coach.create_training_plan(
    "Create a workout called 'Campus Power' scheduled for October 15, 2025 with campus board ladders: 4 sets of 5 rungs with 2 minute rest"
)

print(response)

# Or create a workout without a specific date
response = coach.create_training_plan(
    "Create a workout called 'Quick Session' with hangboard: 3 sets of 10 seconds"
)

print(response)
```

### With Custom API URL

```python
coach = ClimbingCoachSystem(api_base_url="http://localhost:3000")
```

### Direct Method Call

```python
# Bypass the agent and call the method directly
result = coach.create_workout_in_db(
    "Create a beginner hangboard workout with 3 sets of 15 second hangs"
)
print(result)
```

## Testing

A test script has been provided at `backend/test_workout_creation.py`.

**To test:**

1. Start your SvelteKit dev server:
   ```bash
   npm run dev
   ```

2. In another terminal, run the test script:
   ```bash
   cd backend
   python test_workout_creation.py
   ```

## Prerequisites

### Python Dependencies
Make sure you have these installed:
```bash
pip install requests langchain openai chromadb python-dotenv
```

### Environment Setup
Your `.env` file should have:
```
OPENAI_API_KEY=your_openai_api_key_here
```

### Database Setup
Ensure your Prisma database is set up and migrations are run:
```bash
npx prisma migrate dev
```

### Dev Server Running
The API endpoint must be accessible at `http://localhost:5173/api/workouts` (or your configured URL).

## API Endpoint Schema

The agent POSTs to `/api/workouts` with this structure:

```typescript
{
  name: string;           // Required
  description?: string;   // Optional
  userId?: string | null; // Optional
  scheduledDate?: string; // Optional - ISO 8601 date string (e.g., "2025-10-10T00:00:00.000Z")
  exercises: [
    {
      name: string;       // Required
      sets: number;       // Required
      reps?: number;      // Optional
      duration?: number;  // Optional (in seconds)
      rest?: number;      // Optional (in seconds)
    }
  ]
}
```

## Example Requests

The agent can understand various natural language formats:

1. **Simple format:**
   ```
   "Create a hangboard workout with 5 sets of 10 second hangs"
   ```

2. **With specific date:**
   ```
   "Create a workout called 'Power Endurance' scheduled for October 15, 2025 with 
   4x4 bouldering (4 routes, 4 sets) with 2 minute rest, and lock-offs for 3 sets 
   of 5 reps per arm"
   ```

3. **With relative date:**
   ```
   "Make a new workout for tomorrow named 'Campus Training' with campus board for 
   4 sets of 6 rungs with 3 minute rest"
   ```

4. **Multiple exercises with date:**
   ```
   "Create a workout for next Monday called 'Full Body' with campus board for 4 sets 
   of 6 rungs with 3 minute rest, core work for 3 sets of 45 seconds, and antagonist 
   push-ups for 3 sets of 12 reps"
   ```

5. **Without date (date will be null):**
   ```
   "Create a workout called 'Quick Session' with hangboard for 3 sets of 10 seconds"
   ```

### Date Format Support

The LLM can parse various date formats:
- **Specific dates**: "October 10, 2025", "2025-10-15", "Oct 10"
- **Relative dates**: "tomorrow", "next Monday", "in 3 days"
- **No date**: If no date is mentioned, `scheduledDate` will be `null`

## Error Handling

The system handles several error scenarios:

- **JSON parsing errors**: If the LLM returns invalid JSON
- **API request failures**: Network issues or server errors
- **Validation errors**: Missing required fields (caught by API)
- **Database errors**: Handled by the backend API

All errors return a structured JSON response with error details.

## Next Steps

### Potential Enhancements:

1. **Add userId support**: Allow specifying which user the workout belongs to
2. ~~**Schedule workouts**: Add `scheduledDate` field to the workout creation~~ ✅ **COMPLETED**
3. **Workout templates**: Create pre-defined workout templates the agent can reference
4. **Workout updates**: Add ability to edit existing workouts
5. **Workout retrieval**: Add tool to fetch and list existing workouts
6. **Workout validation**: Add more sophisticated validation of exercise combinations
7. **Recurring workouts**: Add support for repeating workouts on a schedule

## Architecture

```
User Request
    ↓
ClimbingCoachSystem.create_training_plan()
    ↓
Coordinator Agent (decides which tool to use)
    ↓
Create_Workout Tool
    ↓
create_workout_in_db() method
    ↓
LLM parses request → JSON
    ↓
HTTP POST to /api/workouts
    ↓
Backend validates & saves to Prisma DB
    ↓
Response returned to user
```

## Troubleshooting

**Issue: "Import requests could not be resolved"**
- Solution: Run `pip install requests`

**Issue: "Connection refused" error**
- Solution: Make sure your dev server is running (`npm run dev`)

**Issue: "Failed to create workout" from API**
- Check the API logs in your dev server terminal
- Verify your database is set up correctly
- Ensure all required fields are present

**Issue: Agent not using Create_Workout tool**
- Make the request more explicit: "Create and save a workout..."
- Try using `create_workout_in_db()` directly to test

## Support

For issues or questions:
1. Check the API logs in your dev server terminal
2. Review the Prisma schema in `prisma/schema.prisma`
3. Test the API endpoint directly with curl or Postman
4. Verify your OpenAI API key is valid and has credits
