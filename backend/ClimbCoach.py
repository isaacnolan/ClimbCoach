import anthropic
from anthropic.types.beta import BetaToolUnionParam
import json
import pandas as pd
from typing import List, Dict, Optional
import requests
from dotenv import load_dotenv
import os

load_dotenv()

class ClimbingCoachSystem:
    def __init__(self, kaggle_gym_path, kaggle_climb_path, google_sheets_url, api_base_url: str = "http://localhost:5173"):
        self.client = anthropic.Anthropic()
        # Allow overriding Claude model via env var; default to a supported model
        self.claude_model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")
        self.kaggle_gym_path = kaggle_gym_path
        self.kaggle_climb_path = kaggle_climb_path
        self.google_sheets_url = google_sheets_url
        self.api_base_url = api_base_url
        
        # Load and store data
        self.gym_data = self.load_kaggle_gym_data(kaggle_gym_path)
        self.climb_data = self.load_kaggle_climb_data(kaggle_climb_path)
        self.sheets_data = self.load_google_sheets_data(google_sheets_url)
        
        # Create indexed knowledge bases
        self.exercise_db = self._build_exercise_db()

    def load_google_sheets_data(self, url):
        """Load data from Google Sheets CSV export"""
        try:
            if '/edit' in url:
                csv_url = url.replace('/edit#gid=', '/export?format=csv&gid=')
                csv_url = csv_url.replace('/edit?gid=', '/export?format=csv&gid=')
            else:
                csv_url = url
            
            df = pd.read_csv(csv_url)
            print(f"Loaded Google Sheets data: {df.shape[0]} rows, {df.shape[1]} columns")
            return df
        except Exception as e:
            print(f"Error loading Google Sheets data: {e}")
            return None
    
    def load_kaggle_gym_data(self, file_path):
        """Load Kaggle gym exercise dataset"""
        try:
            df = pd.read_csv(file_path)
            print(f"Loaded Kaggle gym data: {df.shape[0]} rows, {df.shape[1]} columns")
            return df
        except Exception as e:
            print(f"Error loading Kaggle gym data: {e}")
            return None
    
    def load_kaggle_climb_data(self, file_path):
        """Load Kaggle climbing dataset"""
        try:
            if isinstance(file_path, str):
                df = pd.read_csv(file_path)
                print(f"Loaded Kaggle climb data: {df.shape[0]} rows, {df.shape[1]} columns")
                return df
            elif isinstance(file_path, dict):
                dfs = {}
                for key, path in file_path.items():
                    dfs[key] = pd.read_csv(path)
                    print(f"Loaded {key}: {dfs[key].shape[0]} rows")
                return dfs
        except Exception as e:
            print(f"Error loading Kaggle climb data: {e}")
            return None
    
    def _build_exercise_db(self) -> List[Dict]:
        """Build searchable exercise database"""
        exercises = []
        
        if self.gym_data is not None:
            climbing_relevant_bodyparts = ['forearms', 'shoulders', 'back', 'core', 'abs', 'lats', 'biceps', 'chest', 'triceps']
            
            for _, row in self.gym_data.iterrows():
                try:
                    bodypart = str(row.get('BodyPart', '')).lower()
                    if any(bp in bodypart for bp in climbing_relevant_bodyparts):
                        desc = str(row.get('Desc', ''))
                        exercises.append({
                            'name': row.get('Title', 'Unknown'),
                            'description': desc[:300] if len(desc) > 300 else desc,
                            'bodypart': row.get('BodyPart', ''),
                            'equipment': row.get('Equipment', ''),
                            'level': row.get('Level', ''),
                            'type': row.get('Type', ''),
                            'rating': row.get('Rating', '')
                        })
                except:
                    continue
        
        if self.sheets_data is not None:
            for _, row in self.sheets_data.iterrows():
                try:
                    exercise = {}
                    for col in self.sheets_data.columns:
                        if pd.notna(row[col]):
                            val = str(row[col])
                            # Truncate long text fields
                            if len(val) > 300:
                                val = val[:300]
                            exercise[col] = val
                    if exercise:
                        exercises.append(exercise)
                except:
                    continue
        
        print(f"Built exercise database with {len(exercises)} exercises")
        return exercises
    
    def _build_progression_db(self) -> List[Dict]:
        """Build progression analysis database"""
        progressions = []
        
        if self.climb_data is not None:
            if isinstance(self.climb_data, dict):
                for key, df in self.climb_data.items():
                    if 'grade' in df.columns:
                        grade_analysis = df['grade'].value_counts().head(20)
                        for grade, count in grade_analysis.items():
                            progressions.append({
                                'grade': grade,
                                'count': int(count),
                                'percentage': float(count/len(df)*100),
                                'source': key
                            })
            else:
                if 'grade' in self.climb_data.columns:
                    grade_analysis = self.climb_data['grade'].value_counts().head(20)
                    for grade, count in grade_analysis.items():
                        progressions.append({
                            'grade': grade,
                            'count': int(count),
                            'percentage': float(count/len(self.climb_data)*100),
                            'source': 'climb_data'
                        })
        
        print(f"Built progression database with {len(progressions)} entries")
        return progressions
    
    
    
    def search_exercises(self, query: str, limit: int = 4) -> str:
        """Search for exercises based on query"""
        query_lower = query.lower()
        results = []
        
        for exercise in self.exercise_db:
            score = 0
            exercise_text = json.dumps(exercise).lower()
            
            # Simple keyword matching
            for word in query_lower.split():
                if word in exercise_text:
                    score += 1
            
            if score > 0:
                results.append((score, exercise))
        
        results.sort(reverse=True, key=lambda x: x[0])
        top_results = []
        for _, ex in results[:limit]:
            # Create truncated version
            truncated = {
                'name': ex.get('name', 'Unknown'),
                'bodypart': ex.get('bodypart', ''),
                'equipment': ex.get('equipment', ''),
                'level': ex.get('level', ''),
                # Truncate description to 150 chars
                'description': (ex.get('description', '')[:150] + '...') if len(ex.get('description', '')) > 150 else ex.get('description', '')
            }
            top_results.append(truncated)
    
        return json.dumps(top_results, indent=2)
    
    
    
    def create_training_session_in_db(self, session_data: dict) -> str:
        """Create and save training session to database - accepts pre-parsed JSON"""
        try:
            # Validate required fields
            required_fields = ['name', 'scheduledDate']
            missing_fields = [f for f in required_fields if f not in session_data]
            if missing_fields:
                return json.dumps({
                    "success": False,
                    "error": f"Missing required fields: {', '.join(missing_fields)}"
                }, indent=2)
        
            # POST to API directly - NO nested Claude call
            response = requests.post(
                f"{self.api_base_url}/api/training",
                json=session_data,
                headers={"Content-Type": "application/json"}
            )
        
            if response.status_code == 201:
                created_session = response.json()
                return json.dumps({
                    "success": True,
                    "message": f"Training session '{created_session['name']}' created successfully!",
                    "sessionId": created_session.get('id')
                }, indent=2)
            else:
                return json.dumps({
                    "success": False,
                    "error": response.json().get("error", "Failed to create training session"),
                    "status_code": response.status_code
                }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Error creating training session: {str(e)}"
            }, indent=2)

    def create_workout_in_db(self, workout_request: str) -> str:
        """Create and save workout to database"""
        try:
            # Use Claude to parse the workout request
            parse_response = self.client.messages.create(
                model=self.claude_model,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": f"""Parse this workout request into JSON format:
                    {{
                        "name": "workout name",
                        "description": "brief description",
                        "userId": null,
                        "scheduledDate": "ISO 8601 date or null",
                        "exercises": [
                            {{
                                "name": "exercise name",
                                "sets": number,
                                "reps": number or null,
                                "duration": seconds or null,
                                "rest": seconds or null
                            }}
                        ]
                    }}
                    
                    Today is October 10, 2025. Convert any mentioned dates to ISO 8601 format.
                    
                    Request: {workout_request}
                    
                    Return ONLY valid JSON, no other text."""
                }]
            )
            
            workout_json_str = parse_response.content[0].text.strip()
            
            # Clean up response
            if workout_json_str.startswith("```json"):
                workout_json_str = workout_json_str[7:]
            if workout_json_str.startswith("```"):
                workout_json_str = workout_json_str[3:]
            if workout_json_str.endswith("```"):
                workout_json_str = workout_json_str[:-3]
            workout_json_str = workout_json_str.strip()
            
            workout_data = json.loads(workout_json_str)
            
            # POST to API
            response = requests.post(
                f"{self.api_base_url}/api/workouts",
                json=workout_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                created_workout = response.json()
                return json.dumps({
                    "success": True,
                    "message": f"Workout '{created_workout['name']}' created successfully!",
                    "workout": created_workout
                }, indent=2)
            else:
                return json.dumps({
                    "success": False,
                    "error": response.json().get("error", "Failed to create workout"),
                    "status_code": response.status_code
                }, indent=2)
                
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Error creating workout: {str(e)}"
            }, indent=2)
    
    def get_training_load(self) -> str:
        """Get current training load metrics for the user"""
        try:
            # Fetch training load from API
            response = requests.get(
                f"{self.api_base_url}/api/training-load",
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                return json.dumps({
                    "success": False,
                    "message": "Failed to fetch training load data from API"
                }, indent=2)
            
            data = response.json()
            
            if not data.get('success') or not data.get('trainingLoad'):
                return json.dumps({
                    "success": False,
                    "message": "No training load data available. User may not have any training sessions logged yet."
                }, indent=2)
            
            tl = data['trainingLoad']
            
            # Interpret ACWR
            acwr = tl.get('currentACWR')
            interpretation = "Unknown"
            recommendation = "Unable to provide recommendation without ACWR data."
            
            if acwr is not None:
                if acwr < 0.8:
                    interpretation = "Undertraining"
                    recommendation = "Consider gradually increasing training volume. You have capacity for more work."
                elif 0.8 <= acwr <= 1.5:
                    interpretation = "Optimal"
                    recommendation = "Your training load is well-balanced. Continue progressive training."
                else:
                    interpretation = "Overtraining Risk"
                    recommendation = "CAUTION: High injury risk. Reduce volume, focus on recovery, consider a deload week."
            
            return json.dumps({
                "success": True,
                "training_load": {
                    "acwr": acwr,
                    "acwr_interpretation": interpretation,
                    "acwr_recommendation": recommendation,
                    "acute_load_7day": tl.get('acuteLoad'),
                    "chronic_load_42day": tl.get('chronicLoad'),
                    "max_grade_climbed": f"V{tl.get('maxGrade')}" if tl.get('maxGrade') is not None else "N/A",
                    "recent_sessions_7days": tl.get('recentSessionCount', 0),
                    "average_session_load": round(tl.get('averageSessionLoad', 0), 2),
                    "total_load": round(tl.get('totalLoad', 0), 2),
                    "recent_sessions": tl.get('recentSessions', [])
                },
                "optimal_range": "ACWR between 0.8-1.5 is optimal for progressive training without excessive injury risk"
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Error fetching training load: {str(e)}"
            }, indent=2)
    
    def get_tools(self) -> List[BetaToolUnionParam]:
        """Define Claude tool specifications"""
        return [
            {
                "name": "get_training_load",
                "description": "Get the user's current training load metrics including ACWR (Acute:Chronic Workload Ratio), recent session data, and personalized recommendations. Use this when creating workouts or training plans to ensure proper load management and injury prevention.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "lookup_workouts",
                "description": "Get a list of all available workouts from the database. Use this to find workout IDs when creating training sessions.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "search_exercises",
                "description": """Search for specific exercises from a database of climbing-relevant exercises. Each exercise has these fields:
- name (Title): The name of the exercise
- description (Desc): Detailed description of the exercise
- bodypart: Target muscle group (forearms, shoulders, back, core, abs, lats, biceps, chest, triceps)
- equipment: Required equipment for the exercise
- level: Difficulty level of the exercise
- type: Type of exercise
- rating: User rating score

The search matches these fields against your query terms. Relevant keywords include:
- Body parts: forearms, shoulders, back, core, abs, lats, biceps, chest, triceps
- Common equipment: hangboard, campus board, rings, weights
- Exercise types: strength, endurance, power
- Training goals: finger strength, power endurance, technique""",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query using relevant keywords like body parts (forearms, core), equipment (hangboard), or training goals (finger strength)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of exercises to return (default: 8)",
                            "default": 8
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "create_workout",
                "description": "Create and save a workout to the database. Use when user wants to CREATE and SAVE a workout plan.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "workout_request": {
                            "type": "string",
                            "description": "Full description of the workout including name, exercises with sets/reps/duration, and optional scheduled date. Example: 'Create a workout called Finger Strength scheduled for October 15, 2025 with hangboard training: 5 sets of 10 second hangs with 3 minute rest'"
                        }
                    },
                    "required": ["workout_request"]
                }
            },
            {
                "name": "create_training_session",
                "description": "Create and save a training session to the database. Use when user wants to CREATE and SAVE a training session with climbs and optionally link to a workout.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "session_data": {
                            "type": "object",
                            "description": """JSON object with training session details:
{
  "name": "session name",
  "description": "brief description",
  "scheduledDate": "2025-12-01T00:00:00.000Z",
  "workoutId": "valid-workout-id-or-null",
  "climbs": []
}

For climbs (if any):
{
  "name": "climb name",
  "grade": 2,
  "style": "boulder",
  "status": "sent",
  "attempts": 3,
  "notes": "optional"
}

IMPORTANT:
- Convert V-grades to numbers (V0=0, V1=1, V2=2, etc)
- Date must be ISO 8601 format
- Today is December 2, 2025""",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "scheduledDate": {"type": "string"},
                    "workoutId": {"type": ["string", "null"]},
                    "climbs": {"type": "array"}
                },
                "required": ["name", "scheduledDate"]
            }
        },
        "required": ["session_data"]
    }
}
        ]
    
    def process_tool_call(self, tool_name: str, tool_input: Dict) -> str:
        """Process tool calls and return results"""
        if tool_name == "get_training_load":
            return self.get_training_load()
        elif tool_name == "lookup_workouts":
            return self.lookup_past_workouts()
        elif tool_name == "search_exercises":
            return self.search_exercises(tool_input["query"], tool_input.get("limit", 8))
        elif tool_name == "create_workout":
            return self.create_workout_in_db(tool_input["workout_request"])
        elif tool_name == "create_training_session":
            return self.create_training_session_in_db(tool_input["session_data"])
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
    
    def create_training_plan(self, user_query: str, max_iterations: int = 6, context: dict = None) -> str:
        """Main interface for creating training plans using Claude tool calling"""
        
        # Store training load data if provided
        if context and "training_load" in context:
            self.training_load_data = context["training_load"]
        
        system_prompt = """You are an expert climbing coach with access to comprehensive datasets and specialized tools. 

Your available tools:
- get_training_load: Get user's current training load metrics and ACWR - USE THIS when creating workouts/plans
- lookup_workouts: Get a list of all available workouts from the database (use this BEFORE creating training sessions)
- search_exercises: Find exercises from 2900+ exercise database
- create_workout: Create and save workouts to the database
- create_training_session: Create and save training sessions with climbs and link to existing workouts

When a user asks to create a training session:
1. Use get_training_load FIRST to check their current load and ACWR
2. Use lookup_workouts to find an appropriate existing workout to link
3. Use create_training_session with a valid workoutId from the lookup results
4. Adjust volume/intensity based on their ACWR to prevent overtraining

When a user asks to create or save a workout:
1. Use get_training_load FIRST to check their current load and ACWR
2. Use create_workout tool, adjusting volume/intensity based on their training load

When a user asks to log climbs:
1. Use lookup_workouts first to find an appropriate workout
2. Then use create_training_session

Provide comprehensive, data-driven coaching advice based on the tools and data available."""
        
        messages = [{"role": "user", "content": user_query}]
        
        for iteration in range(max_iterations):
            response = self.client.messages.create(
                model=self.claude_model,
                max_tokens=2048,
                system=system_prompt,
                tools=self.get_tools(),
                messages=messages
            )
            
            # Check if we're done (no tool use)
            if response.stop_reason == "end_turn":
                final_response = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        final_response += block.text
                return final_response
            
            # Process tool calls
            if response.stop_reason == "tool_use":
                # Add assistant's response to messages
                messages.append({"role": "assistant", "content": response.content})
                
                # Process each tool use
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        print(f"\nUsing tool: {block.name}")
                        print(f"Input: {json.dumps(block.input, indent=2)}")
                        
                        result = self.process_tool_call(block.name, block.input)
                        print(f"Result preview: {result[:200]}...")
                        
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        })
                
                # Add tool results to messages
                messages.append({"role": "user", "content": tool_results})
            else:
                # Unexpected stop reason
                break
        
        return "Maximum iterations reached. Please try rephrasing your question."
    
    def analyze_dataset_stats(self):
        """Print statistics about loaded datasets"""
        print("\n=== Dataset Statistics ===")
        print(f"Exercise database: {len(self.exercise_db)} exercises")
    
    def lookup_past_workouts(self) -> str:
        """Get list of available workouts from the database"""
        try:
            # GET request to workouts API
            response = requests.get(
                f"{self.api_base_url}/api/workouts",
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                workouts = response.json()
                # Simplify workouts to reduce token usage
                simplified_workouts = []
                for w in workouts[:15]:  # Limit to 15
                    exercise_names = []
                    if 'exercises' in w and w['exercises']:
                        exercise_names = [ex.get('name', 'Exercise') for ex in w['exercises'][:5]]
                        if len(w['exercises']) > 5:
                            exercise_names.append(f"...+{len(w['exercises']) - 5} more")
                
                    simplified_workouts.append({
                        'id': w.get('id'),
                        'name': w.get('name', 'Unnamed')[:50],
                        'date': w.get('scheduledDate', '')[:10] if w.get('scheduledDate') else None,
                        'exercises': ', '.join(exercise_names) if exercise_names else 'No exercises'
                    })
            
                return json.dumps({
                    "success": True,
                    "total": len(workouts),
                    "workouts": simplified_workouts
                }, indent=2)
            else:
                return json.dumps({
                    "success": False,
                    "error": "Failed to fetch workouts",
                    "status_code": response.status_code
                }, indent=2)
                
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Error fetching workouts: {str(e)}"
            }, indent=2)


# Usage example
if __name__ == "__main__":
    coach = ClimbingCoachSystem(
        kaggle_gym_path="data/gym_data.csv",
        kaggle_climb_path="climb_dataset.csv",
        google_sheets_url="https://docs.google.com/spreadsheets/d/1J6d45EqIlIsIqNdi2X-Zl-EGFxf9d9T3R_W55xrpEAs/export?format=csv&gid=1650492946"
    )
    
    coach.analyze_dataset_stats()
    
    # Print example exercises from the database
    print("\n=== Exercise Database Sample ===")
    for i, exercise in enumerate(coach.exercise_db[:10]):  # Print first 10 exercises
        print(f"\nExercise {i+1}:")
        for key, value in exercise.items():
            print(f"{key}: {value}")
    
    print("\n=== Example Search Results ===")
    # Try some example searches
    search_queries = [
        "forearm strength training",
        "hangboard finger exercises",
        "core workout for climbing",
        "shoulder mobility exercises"
    ]
    
    for query in search_queries:
        print(f"\nSearch query: {query}")
        print("-" * 50)
        results = json.loads(coach.search_exercises(query, limit=3))
        for result in results:
            print(f"\nName: {result.get('name', 'N/A')}")
            print(f"Body Part: {result.get('bodypart', 'N/A')}")
            print(f"Description: {result.get('description', 'N/A')[:100]}...")