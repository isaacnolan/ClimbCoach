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
    
    
    
    def create_workout_in_db(self, workout_request: str) -> str:
        """Create and save workout to database"""
        try:
            # Use Claude to parse the workout request
            parse_response = self.client.messages.create(
                model="claude-sonnet-4-5",
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
                "name": "search_exercises",
                "description": "Search for specific exercises from a comprehensive database of 2900+ exercises. Use this to find exercises for specific body parts, equipment, or training goals.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query describing the type of exercise needed (e.g., 'finger strength', 'shoulder mobility', 'core exercises')"
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
            }
        ]
    
    def process_tool_call(self, tool_name: str, tool_input: Dict) -> str:
        """Process tool calls and return results"""
        if tool_name == "search_exercises":
            return self.search_exercises(tool_input["query"], tool_input.get("limit", 8))
        elif tool_name == "create_workout":
            return self.create_workout_in_db(tool_input["workout_request"])
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
    
    def create_training_plan(self, user_query: str, max_iterations: int = 6) -> str:
        """Main interface for creating training plans using Claude tool calling"""
        
        system_prompt = """You are an expert climbing coach with access to comprehensive datasets and specialized tools. 

Your available tools:
- search_exercises: Find exercises from 2900+ exercise database
- create_workout: Create and save workouts to the database

When a user asks you to create or save a workout, use the create_workout tool with the full workout description.

Provide comprehensive, data-driven coaching advice based on the tools and data available."""
        
        messages = [{"role": "user", "content": user_query}]
        
        for iteration in range(max_iterations):
            response = self.client.messages.create(
                model="claude-sonnet-4-5",
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


# Usage example
if __name__ == "__main__":
    coach = ClimbingCoachSystem(
        kaggle_gym_path="gym_exercise_data.csv",
        kaggle_climb_path="climb_dataset.csv",
        google_sheets_url="https://docs.google.com/spreadsheets/d/1J6d45EqIlIsIqNdi2X-Zl-EGFxf9d9T3R_W55xrpEAs/export?format=csv&gid=1650492946"
    )
    
    coach.analyze_dataset_stats()
    
    # Example queries
    queries = [
        "Create a workout called 'V5 Power Training' scheduled for October 15, 2025 with campus board ladders: 4 sets of 6 rungs with 3 minute rest, and hangboard repeaters: 6 sets of 7 seconds with 3 seconds off"    ]
    
    for query in queries:
        print(f"\n{'='*70}")
        print(f"Query: {query}")
        print('='*70)
        response = coach.create_training_plan(query)
        print(response)
        print('='*70)