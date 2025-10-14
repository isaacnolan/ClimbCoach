# Claude Agent V2 - Database Integration Update

## Overview

Updated `claude_agent_v2.py` to include workout creation and database writing capabilities while preserving all existing functionality with Kaggle datasets and Google Sheets integration.

## Changes Made

### ✅ What Was Added

1. **Import Statement**
   - Added `import requests` for HTTP API calls

2. **Constructor Enhancement**
   - Added `api_base_url` parameter (default: `http://localhost:5173`)
   - Maintains all existing parameters: `kaggle_gym_path`, `kaggle_climb_path`, `google_sheets_url`

3. **New Method: `create_workout_in_db()`**
   - Parses natural language workout requests using LLM
   - Supports scheduled dates (ISO 8601 format)
   - Handles specific dates: "October 15, 2025"
   - Handles relative dates: "tomorrow", "next Monday"
   - POSTs to `/api/workouts` endpoint
   - Returns structured success/error responses

4. **New Tool: `Create_Workout`**
   - Added to the tools list in `setup_agents()`
   - Allows coordinator agent to create and save workouts
   - Works alongside existing tools

5. **Enhanced `create_training_plan()` Method**
   - Updated prompt to recognize workout creation requests
   - Agent can now decide when to create vs. advise
   - Maintains all existing functionality

### ✅ What Was Preserved

All existing functionality remains intact:
- ✅ Kaggle gym dataset integration (2900+ exercises)
- ✅ Kaggle climbing dataset integration (8a.nu data)
- ✅ Google Sheets integration
- ✅ Exercise prescription from comprehensive database
- ✅ Progression planning based on climbing data
- ✅ Technique coaching
- ✅ Injury prevention advice
- ✅ Route analysis
- ✅ All vectorstore creation methods
- ✅ All analysis methods
- ✅ Dataset statistics function

## Usage

### Initialize the System

```python
from claude_agent_v2 import ClimbingCoachSystem

# Initialize with dataset paths and API URL
coach = ClimbingCoachSystem(
    kaggle_gym_path="gym_exercise_data.csv",
    kaggle_climb_path="climb_dataset.csv",
    google_sheets_url="https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/export?format=csv&gid=YOUR_GID",
    api_base_url="http://localhost:5173"  # Optional, defaults to localhost:5173
)
```

### Create and Save Workouts

```python
# Create a workout with a scheduled date
response = coach.create_training_plan(
    "Create a workout called 'Power Training' scheduled for October 15, 2025 "
    "with campus board: 4 sets of 6 rungs with 3 minute rest, "
    "and hangboard: 5 sets of 10 seconds with 2 minute rest"
)
print(response)
```

### Get Training Advice (Existing Functionality)

```python
# All existing queries still work
response = coach.create_training_plan(
    "Create a 6-week plan for a V3 climber aiming to reach V5"
)

response = coach.create_training_plan(
    "Help me improve my finger strength using exercises from the database"
)

response = coach.create_training_plan(
    "What does the climbing data tell us about grade progression?"
)
```

## New Capabilities

### Workout Creation Examples

1. **With specific date:**
   ```python
   "Create a workout called 'Finger Power' scheduled for October 20, 2025 with hangboard: 5 sets of 10 seconds"
   ```

2. **With relative date:**
   ```python
   "Create a workout for tomorrow called 'Quick Session' with campus board: 3 sets of 5 rungs"
   ```

3. **Without date:**
   ```python
   "Create a workout called 'Core Training' with planks: 3 sets of 60 seconds"
   ```

4. **Complex workout:**
   ```python
   "Create a workout scheduled for next Monday called 'Full Training' with:
   - Campus board ladders: 4 sets of 6 rungs with 3 minute rest
   - Hangboard repeaters: 6 sets of 7 seconds on, 3 seconds off
   - Core work: 3 sets of 45 seconds with 90 second rest"
   ```

## Tools Available to the Agent

The coordinator agent now has 6 tools:

1. **Exercise_Prescription** - Recommend exercises from 2900+ gym exercise database
2. **Progression_Planning** - Plan grade progressions based on 8a.nu climbing data
3. **Technique_Coaching** - Provide technique advice from training data
4. **Injury_Prevention** - Safety and injury prevention from exercise database
5. **Route_Analysis** - Route strategy advice from route database
6. **Create_Workout** ✨ **NEW** - Create and save workouts to database

## API Integration

### Endpoint
POSTs to: `{api_base_url}/api/workouts`

### JSON Structure
```json
{
  "name": "Workout Name",
  "description": "Brief description",
  "userId": null,
  "scheduledDate": "2025-10-15T00:00:00.000Z",
  "exercises": [
    {
      "name": "Exercise name",
      "sets": 4,
      "reps": 6,
      "duration": null,
      "rest": 180
    }
  ]
}
```

## Prerequisites

### Python Dependencies
```bash
pip install langchain openai chromadb pandas python-dotenv requests
```

### Environment Variables
`.env` file should contain:
```
OPENAI_API_KEY=your_openai_api_key_here
```

### Running Backend Server
The SvelteKit dev server must be running:
```bash
npm run dev
```

### Datasets Required
- Kaggle gym exercise dataset (CSV)
- Kaggle climbing dataset (CSV) - 8a.nu data
- Google Sheets URL with climbing training data

## Architecture

```
User Request
    ↓
ClimbingCoachSystem.create_training_plan()
    ↓
Coordinator Agent analyzes intent
    ↓
    ├─→ Create workout? → Create_Workout Tool → API → Database
    ├─→ Exercise advice? → Exercise_Prescription Tool → Kaggle Gym DB
    ├─→ Progression plan? → Progression_Planning Tool → Climbing Data
    ├─→ Technique help? → Technique_Coaching Tool → Training Data
    ├─→ Injury prevention? → Injury_Prevention Tool → Exercise DB
    └─→ Route analysis? → Route_Analysis Tool → Route Data
```

## Comparison: V1 vs V2

| Feature | claude_agent_flow.py (V1) | claude_agent_v2.py (V2) |
|---------|---------------------------|-------------------------|
| Workout Creation | ✅ Yes | ✅ Yes |
| Scheduled Dates | ✅ Yes | ✅ Yes |
| Kaggle Gym Dataset | ❌ No | ✅ Yes (2900+ exercises) |
| Kaggle Climb Dataset | ❌ No | ✅ Yes (8a.nu data) |
| Google Sheets | ❌ No | ✅ Yes |
| Exercise Database | Limited | ✅ Comprehensive |
| Route Analysis | ❌ No | ✅ Yes |
| Grade Progression Data | Limited | ✅ Data-driven |
| Technique Database | Limited | ✅ From datasets |

## Testing

### Test Workout Creation

```python
coach = ClimbingCoachSystem(
    kaggle_gym_path="gym_exercise_data.csv",
    kaggle_climb_path="climb_dataset.csv",
    google_sheets_url="YOUR_SHEETS_URL"
)

# Test creating a workout
response = coach.create_training_plan(
    "Create a workout called 'Test Session' for tomorrow with hangboard: 3 sets of 10 seconds"
)
print(response)
```

### View Dataset Statistics

```python
coach.analyze_dataset_stats()
```

This will show:
- Number of exercises in vectorstore
- Number of progression documents
- Number of route documents
- Number of technique documents
- Number of injury prevention documents

## Benefits of V2

1. **Comprehensive Exercise Database** - 2900+ exercises vs. limited hardcoded list
2. **Real Climbing Data** - Grade progressions from actual 8a.nu data
3. **Flexible Training Data** - Integrate custom Google Sheets
4. **Database Integration** - Save workouts with scheduled dates
5. **Multi-Tool Agent** - 6 specialized tools for comprehensive coaching
6. **Data-Driven Advice** - Recommendations based on real datasets

## Next Steps

Potential enhancements:
1. Add userId support for user-specific workouts
2. Retrieve and display existing workouts
3. Update/modify existing workouts
4. Create workout templates from popular routes
5. Generate workouts based on user's climbing data analysis
6. Add recurring workout scheduling
7. Integrate workout history into progression planning

## Notes

- The agent intelligently decides which tool to use based on user intent
- All existing functionality is preserved - nothing was removed
- The system gracefully handles missing datasets with fallback data
- Error handling is comprehensive for API calls and data parsing
- Date parsing is intelligent (supports "tomorrow", "next Monday", etc.)
