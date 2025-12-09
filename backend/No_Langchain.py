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
        self.sheets_data = self.load_google_gym_data(google_sheets_url)
        
        # Create indexed knowledge bases
        self.exercise_db = self._build_exercise_db()
    
    def load_google_gym_data(self, file_path):
        """Load Google gym exercise dataset"""
        try:
            df = pd.read_csv(file_path)
            print(f"Loaded Google gym data: {df.shape[0]} rows, {df.shape[1]} columns")
            return df
        except Exception as e:
            print(f"Error loading Google gym data: {e}")
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
                        exercises.append({
                            'name': row.get('Title', 'Unknown'),
                            'description': row.get('Desc', ''),
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
                    exercise = {col: row[col] for col in self.sheets_data.columns if pd.notna(row[col])}
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
    
    
    
    def search_exercises(self, query: str, limit: int = 8) -> str:
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
        top_results = [ex for _, ex in results[:limit]]
        
        return json.dumps(top_results, indent=2)
    
    
    
    def create_training_session_in_db(self, session_request: str) -> str:
        """Create and save training session to database"""
        try:
            # Use Claude to parse the training session request
            parse_response = self.client.messages.create(
                model=self.claude_model,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": f"""Parse this training session request into JSON format. Follow these requirements exactly:

1. REQUIRED: Convert V-grades to numbers (V0=0, V1=1, V2=2, etc)
2. REQUIRED: workoutId must be a valid ID from lookup_workouts
3. REQUIRED: dates must be in ISO 8601 format
4. REQUIRED: grade must be a number, not a string
5. REQUIRED: style must be exactly "boulder", "sport", or "trad"
6. REQUIRED: status must be exactly "sent", "attempt", or "project"

Example request: "Create a session called Evening Projecting for Nov 5 2025, link to workout ID abc123. Climbed: warmed up on V2, sent after 2 attempts. Then worked V4 project for 5 attempts."

Example response:
{{
    "name": "Evening Projecting",
    "description": "Bouldering session with warmup and project work",
    "scheduledDate": "2025-11-05T00:00:00.000Z",
    "workoutId": "abc123",
    "climbs": [
        {{
            "name": "Warmup Problem",
            "grade": 2,
            "style": "boulder",
            "status": "sent",
            "attempts": 2,
            "notes": "Warmup climb"
        }},
        {{
            "name": "Project Problem",
            "grade": 4,
            "style": "boulder",
            "status": "project",
            "attempts": 5,
            "notes": "Working on sequences"
        }}
    ]
}}

Today is October 10, 2025. Convert any mentioned dates to ISO 8601 format.

Parse this training session request into the same format:
Request: {session_request}

Return ONLY valid JSON, no other text."""
                }]
            )
            
            session_json_str = parse_response.content[0].text.strip()
            
            # Clean up response
            if session_json_str.startswith("```json"):
                session_json_str = session_json_str[7:]
            if session_json_str.startswith("```"):
                session_json_str = session_json_str[3:]
            if session_json_str.endswith("```"):
                session_json_str = session_json_str[:-3]
            session_json_str = session_json_str.strip()
            
            session_data = json.loads(session_json_str)
            
            # POST to API
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
                    "session": created_session
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
    
    def get_tools(self) -> List[BetaToolUnionParam]:
        """Define Claude tool specifications"""
        return [
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
                        "session_request": {
                            "type": "string",
                            "description": "Full description of the training session including name, scheduled date, climbs completed (with grades, style, and attempts), and optionally a workout ID to link. Example: 'Create a training session called Evening Bouldering for October 15, 2025 where I sent two V4s after 3 attempts each and projected a V6 with 5 attempts'"
                        }
                    },
                    "required": ["session_request"]
                }
            },
            {
                "name": "find_similar_climbers",
                "description": """Find climbers with similar physical traits and climbing ability from the training database. 
                
    ONLY use this tool when the user mentions their own physical characteristics or climbing level. Examples of when to use:
    - "I'm 5'10\" and climb V5"
    - "I weigh 165 lbs and my max grade is 5.12a"
    - "I'm a beginner climber, 6 feet tall"
    - "I climb V8 and I'm 150 pounds"

    DO NOT use this tool for:
    - General training advice without user stats
    - Creating workouts or sessions
    - Looking up exercise information

    This tool helps personalize training recommendations by finding climbers with similar profiles.""",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "user_profile": {
                            "type": "object",
                            "description": "User's physical and climbing characteristics",
                            "properties": {
                                "height": {
                                    "type": "number",
                                    "description": "Height in inches or cm (specify unit)"
                                },
                                "weight": {
                                    "type": "number",
                                    "description": "Weight in pounds or kg (specify unit)"
                                },
                                "climbing_grade": {
                                    "type": "string",
                                    "description": "Current climbing grade (e.g., V5, 5.12a, 7a)"
                                },
                                "experience_level": {
                                    "type": "string",
                                    "description": "Beginner, Intermediate, Advanced, or Elite"
                                }
                            }
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of similar climbers to return (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["user_profile"]
                }
            }
        ]
    
    def process_tool_call(self, tool_name: str, tool_input: Dict) -> str:
        """Process tool calls and return results"""
        if tool_name == "lookup_workouts":
            return self.lookup_past_workouts()
        elif tool_name == "search_exercises":
            return self.search_exercises(tool_input["query"], tool_input.get("limit", 8))
        elif tool_name == "create_workout":
            return self.create_workout_in_db(tool_input["workout_request"])
        elif tool_name == "create_training_session":
            return self.create_training_session_in_db(tool_input["session_request"])
        elif tool_name == "find_similar_climbers":
            return self.find_similar_climbers(tool_input["user_profile"], tool_input.get("limit", 5))
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
    
    def create_training_plan(self, user_query: str, max_iterations: int = 6) -> str:
        """Main interface for creating training plans using Claude tool calling"""
        
        system_prompt = """You are an expert climbing coach with access to comprehensive datasets and specialized tools. 

Your available tools:
- lookup_workouts: Get a list of all available workouts from the database (use this BEFORE creating training sessions)
- search_exercises: Find exercises from 2900+ exercise database
- create_workout: Create and save workouts to the database
- create_training_session: Create and save training sessions with climbs and link to existing workouts
- find_similar_climbers: Find climbers with similar physical traits and ability (ONLY use when user shares their stats)

IMPORTANT - When to use find_similar_climbers:
 USE when user mentions their physical characteristics:
  - Height (e.g., "I'm 5'10\"", "I'm 180cm tall")
  - Weight (e.g., "I weigh 165 lbs", "I'm 75kg")
  - Climbing grade (e.g., "I climb V5", "my max is 5.12a")
  - Experience level (e.g., "I'm a beginner", "I'm intermediate")

 DO NOT USE for:
  - General training questions without user stats
  - Creating workouts or logging sessions
  - Exercise searches

Workflow when user shares their stats:
1. Use find_similar_climbers to get profiles of similar climbers
2. Analyze what training approaches worked for them
3. Use search_exercises to find appropriate exercises
4. Provide personalized recommendations based on similar climbers' success

When a user asks to create a training session:
1. ALWAYS use lookup_workouts first to find an appropriate existing workout to link
2. Then use create_training_session with a valid workoutId from the lookup results

When a user asks to:
- Create or save a workout: use create_workout tool
- Log climbs or create a training session: use lookup_workouts THEN create_training_session

Provide comprehensive, data-driven coaching advice based on the tools and data available."""
        
        messages = [{"role": "user", "content": user_query}]
        
        for iteration in range(max_iterations):
            response = self.client.messages.create(
                model=self.claude_model,
                max_tokens=4096,
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
                         # Handle result preview safely
                        if isinstance(result, str):
                            print(f"Result preview: {result[:200]}...")
                        else:
                            print(f"Result preview: {str(result)[:200]}...")
                        
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
    
    def find_similar_climbers(self, user_profile: Dict, limit: int = 5) -> str:
        """Find climbers with similar physical traits and climbing ability"""
        if self.sheets_data is None:
            return json.dumps({"error": "Training data not loaded"})
        
        df = self.sheets_data.copy()
        
        # Extract user characteristics
        user_height = user_profile.get('height')
        user_weight = user_profile.get('weight')
        user_grade = user_profile.get('climbing_grade')
        user_level = user_profile.get('experience_level')
        
        # Calculate similarity scores
        df['similarity_score'] = 0.0
        
        # Height matching (if column exists)
        height_cols = [col for col in df.columns if 'height' in col.lower()]
        if user_height and height_cols:
            height_col = height_cols[0]
            df['height_numeric'] = pd.to_numeric(df[height_col], errors='coerce')
            df['height_diff'] = abs(df['height_numeric'] - user_height)
            # Normalize: smaller difference = higher score (0-1 scale)
            max_diff = df['height_diff'].max()
            if max_diff > 0:
                df['height_score'] = 1 - (df['height_diff'] / max_diff)
                df['similarity_score'] += df['height_score'] * 0.3  # 30% weight
        
        # Weight matching (if column exists)
        weight_cols = [col for col in df.columns if 'weight' in col.lower()]
        if user_weight and weight_cols:
            weight_col = weight_cols[0]
            df['weight_numeric'] = pd.to_numeric(df[weight_col], errors='coerce')
            df['weight_diff'] = abs(df['weight_numeric'] - user_weight)
            max_diff = df['weight_diff'].max()
            if max_diff > 0:
                df['weight_score'] = 1 - (df['weight_diff'] / max_diff)
                df['similarity_score'] += df['weight_score'] * 0.3  # 30% weight
        
        # Grade matching (if column exists)
        grade_cols = [col for col in df.columns if 'grade' in col.lower() or 'level' in col.lower()]
        if user_grade and grade_cols:
            grade_col = grade_cols[0]
            # Simple string matching for now
            df['grade_match'] = df[grade_col].astype(str).str.contains(user_grade, case=False, na=False)
            df['similarity_score'] += df['grade_match'].astype(float) * 0.4  # 40% weight
        
        # Remove rows with no similarity
        df = df[df['similarity_score'] > 0].copy()
        
        # Sort by similarity and get top matches
        df = df.sort_values('similarity_score', ascending=False).head(limit)
        
        # Build results
        results = []
        for _, row in df.iterrows():
            climber = {
                "similarity_score": float(row['similarity_score']),
                "profile": {}
            }
            
            # Include relevant columns
            relevant_cols = ['height', 'weight', 'grade', 'level', 'experience', 'age']
            for col in df.columns:
                if any(term in col.lower() for term in relevant_cols):
                    if pd.notna(row[col]):
                        climber['profile'][col] = str(row[col])
            
            results.append(climber)
        
        return json.dumps({
            "user_profile": user_profile,
            "similar_climbers": results,
            "count": len(results),
            "message": f"Found {len(results)} climbers with similar characteristics"
        }, indent=2)



# Usage example
if __name__ == "__main__":
    coach = ClimbingCoachSystem(
        kaggle_gym_path="gym_exercise_data.csv",
        kaggle_climb_path="climb_dataset.csv",
        google_sheets_url="climbData/google_sheets.csv"
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