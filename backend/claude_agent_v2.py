from langchain.agents import AgentType, initialize_agent, Tool
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
import openai
from dotenv import load_dotenv
import os
import pandas as pd
from typing import List, Dict
import json
import requests

load_dotenv()

# Now you can access your environment variables
openai_api_key = os.getenv('OPENAI_API_KEY')

class ClimbingCoachSystem:
    def __init__(self, kaggle_gym_path, kaggle_climb_path, google_sheets_url, api_base_url: str = "http://localhost:5173"):
        self.llm = OpenAI(temperature=0.7)
        self.embeddings = OpenAIEmbeddings()
        self.kaggle_gym_path = kaggle_gym_path
        self.kaggle_climb_path = kaggle_climb_path
        self.google_sheets_url = google_sheets_url
        self.api_base_url = api_base_url
        self.setup_knowledge_bases()
        self.setup_agents()
    
    def load_google_sheets_data(self, url):
        """Load data from Google Sheets CSV export"""
        try:
            # Convert Google Sheets URL to CSV export format
            if '/edit' in url:
                csv_url = url.replace('/edit#gid=', '/export?format=csv&gid=')
                csv_url = csv_url.replace('/edit?gid=', '/export?format=csv&gid=')
            else:
                csv_url = url
            
            df = pd.read_csv(csv_url)
            print(f"Loaded Google Sheets data: {df.shape[0]} rows, {df.shape[1]} columns")
            print(f"Columns: {list(df.columns)}")
            return df
        except Exception as e:
            print(f"Error loading Google Sheets data: {e}")
            return None
    
    def load_kaggle_gym_data(self, file_path):
        """Load Kaggle gym exercise dataset"""
        try:
            df = pd.read_csv(file_path)
            print(f"Loaded Kaggle gym data: {df.shape[0]} rows, {df.shape[1]} columns")
            print(f"Columns: {list(df.columns)}")
            return df
        except Exception as e:
            print(f"Error loading Kaggle gym data: {e}")
            return None
    
    def load_kaggle_climb_data(self, file_path):
        """Load Kaggle climbing dataset (8a.nu data)"""
        try:
            # Handle both single file and multiple files
            if isinstance(file_path, str):
                df = pd.read_csv(file_path)
                print(f"Loaded Kaggle climb data: {df.shape[0]} rows, {df.shape[1]} columns")
                print(f"Columns: {list(df.columns)}")
                return df
            elif isinstance(file_path, dict):
                # Multiple files
                dfs = {}
                for key, path in file_path.items():
                    dfs[key] = pd.read_csv(path)
                    print(f"Loaded {key}: {dfs[key].shape[0]} rows, {dfs[key].shape[1]} columns")
                return dfs
        except Exception as e:
            print(f"Error loading Kaggle climb data: {e}")
            return None
    
    def setup_knowledge_bases(self):
        """Create specialized knowledge bases from Kaggle datasets only"""
        
        # Load all datasets
        gym_data = self.load_kaggle_gym_data(self.kaggle_gym_path)
        climb_data = self.load_kaggle_climb_data(self.kaggle_climb_path)
        sheets_data = self.load_google_sheets_data(self.google_sheets_url)
        
        if gym_data is None and climb_data is None and sheets_data is None:
            raise ValueError("No datasets could be loaded. Please check your file paths and URLs.")
        
        # Create knowledge bases from actual data only
        self.exercise_vectorstore = self.create_exercise_vectorstore(gym_data, sheets_data)
        self.progression_vectorstore = self.create_progression_vectorstore(climb_data, sheets_data)
        self.technique_vectorstore = self.create_technique_vectorstore(sheets_data)
        self.route_vectorstore = self.create_route_vectorstore(climb_data)
        self.injury_prevention_vectorstore = self.create_injury_prevention_vectorstore(gym_data, sheets_data)
    
    def create_exercise_vectorstore(self, gym_data, sheets_data):
        """Create exercise database from Kaggle gym data and Google Sheets"""
        
        all_exercises = []
        
        # Process Kaggle gym data
        if gym_data is not None:
            # Filter for climbing-relevant exercises
            climbing_relevant_bodyparts = ['forearms', 'shoulders', 'back', 'core', 'abs', 'lats', 'biceps', 'chest', 'triceps']
            climbing_relevant_types = ['strength', 'cardio', 'flexibility', 'plyometrics', 'powerlifting', 'olympic', 'stretching']
            
            for _, row in gym_data.iterrows():
                try:
                    bodypart = str(row.get('BodyPart', '')).lower()
                    exercise_type = str(row.get('Type', '')).lower()
                    
                    # Include exercise if it targets climbing-relevant body parts or types
                    if any(bp in bodypart for bp in climbing_relevant_bodyparts) or \
                       any(et in exercise_type for et in climbing_relevant_types):
                        
                        exercise_text = f"Exercise: {row.get('Title', 'Unknown')}"
                        if pd.notna(row.get('Desc', '')):
                            exercise_text += f", Description: {row.get('Desc', '')}"
                        if pd.notna(row.get('BodyPart', '')):
                            exercise_text += f", Target Muscles: {row.get('BodyPart', '')}"
                        if pd.notna(row.get('Equipment', '')):
                            exercise_text += f", Equipment: {row.get('Equipment', '')}"
                        if pd.notna(row.get('Level', '')):
                            exercise_text += f", Difficulty: {row.get('Level', '')}"
                        if pd.notna(row.get('Type', '')):
                            exercise_text += f", Type: {row.get('Type', '')}"
                        if pd.notna(row.get('Rating', '')):
                            exercise_text += f", Rating: {row.get('Rating', '')}"
                        
                        all_exercises.append({
                            'text': exercise_text,
                            'source': 'kaggle_gym',
                            'metadata': row.to_dict()
                        })
                except Exception as e:
                    continue
        
        # Process Google Sheets climbing-specific data
        if sheets_data is not None:
            for _, row in sheets_data.iterrows():
                try:
                    exercise_text = ""
                    metadata = {}
                    
                    for col in sheets_data.columns:
                        value = row.get(col, '')
                        if pd.notna(value) and str(value).strip():
                            exercise_text += f"{col}: {value}, "
                            metadata[col] = value
                    
                    if exercise_text:
                        all_exercises.append({
                            'text': exercise_text.rstrip(', '),
                            'source': 'google_sheets',
                            'metadata': metadata
                        })
                except Exception as e:
                    continue
        
        if not all_exercises:
            raise ValueError("No valid exercises found in datasets")
        
        # Create documents for vector store
        docs = []
        for exercise in all_exercises:
            docs.append(Document(
                page_content=exercise['text'], 
                metadata=exercise['metadata']
            ))
        
        print(f"Created exercise vectorstore with {len(docs)} exercises")
        return Chroma.from_documents(docs, self.embeddings)
    
    def create_progression_vectorstore(self, climb_data, sheets_data):
        """Create grade progression data from climbing datasets"""
        
        progression_docs = []
        
        # Process climbing dataset for grade analysis
        if climb_data is not None:
            if isinstance(climb_data, dict):
                # Multiple dataframes (routes, ascents, etc.)
                for key, df in climb_data.items():
                    if 'grade' in df.columns:
                        grade_analysis = self._analyze_grades(df, key)
                        progression_docs.extend(grade_analysis)
            else:
                # Single dataframe
                if 'grade' in climb_data.columns:
                    grade_analysis = self._analyze_grades(climb_data, 'climb_data')
                    progression_docs.extend(grade_analysis)
        
        # Process Google Sheets for progression insights
        if sheets_data is not None:
            # Look for progression-related columns
            progression_cols = [col for col in sheets_data.columns if any(keyword in col.lower() 
                               for keyword in ['grade', 'level', 'ability', 'progression', 'week', 'phase'])]
            
            for _, row in sheets_data.iterrows():
                try:
                    prog_text = ""
                    metadata = {}
                    
                    for col in progression_cols:
                        value = row.get(col, '')
                        if pd.notna(value) and str(value).strip():
                            prog_text += f"{col}: {value}, "
                            metadata[col] = value
                    
                    if prog_text:
                        progression_docs.append(Document(
                            page_content=prog_text.rstrip(', '),
                            metadata=metadata
                        ))
                except Exception as e:
                    continue
        
        if not progression_docs:
            # Create minimal fallback if no progression data found
            progression_docs.append(Document(
                page_content="No specific progression data available from datasets",
                metadata={'source': 'system'}
            ))
        
        print(f"Created progression vectorstore with {len(progression_docs)} documents")
        return Chroma.from_documents(progression_docs, self.embeddings)
    
    def _analyze_grades(self, df, source_name):
        """Analyze grade distribution in climbing data"""
        docs = []
        
        if 'grade' in df.columns:
            # Grade distribution analysis
            grade_counts = df['grade'].value_counts()
            for grade, count in grade_counts.head(20).items():
                text = f"Grade Analysis - {source_name}: Grade {grade} appears {count} times, representing {count/len(df)*100:.1f}% of routes"
                docs.append(Document(
                    page_content=text,
                    metadata={'grade': grade, 'count': count, 'source': source_name}
                ))
        
        # Additional analysis based on available columns
        for col in ['difficulty', 'style', 'type', 'rating']:
            if col in df.columns:
                col_counts = df[col].value_counts()
                for value, count in col_counts.head(10).items():
                    text = f"{col.title()} Analysis - {source_name}: {value} appears {count} times"
                    docs.append(Document(
                        page_content=text,
                        metadata={col: value, 'count': count, 'source': source_name}
                    ))
        
        return docs
    
    def create_technique_vectorstore(self, sheets_data):
        """Create technique knowledge from Google Sheets data"""
        
        technique_docs = []
        
        if sheets_data is not None:
            # Look for technique-related content
            technique_cols = [col for col in sheets_data.columns if any(keyword in col.lower() 
                             for keyword in ['technique', 'movement', 'skill', 'notes', 'focus', 'tip'])]
            
            for _, row in sheets_data.iterrows():
                try:
                    for col in technique_cols:
                        value = row.get(col, '')
                        if pd.notna(value) and str(value).strip():
                            technique_docs.append(Document(
                                page_content=f"{col}: {value}",
                                metadata={'column': col, 'source': 'google_sheets'}
                            ))
                except Exception as e:
                    continue
        
        if not technique_docs:
            # Create minimal fallback
            technique_docs.append(Document(
                page_content="No specific technique data available from datasets",
                metadata={'source': 'system'}
            ))
        
        print(f"Created technique vectorstore with {len(technique_docs)} documents")
        return Chroma.from_documents(technique_docs, self.embeddings)
    
    def create_route_vectorstore(self, climb_data):
        """Create route analysis from climbing dataset"""
        
        route_docs = []
        
        if climb_data is not None:
            if isinstance(climb_data, dict):
                # Multiple dataframes
                for key, df in climb_data.items():
                    if 'route' in key.lower() or any(col in df.columns for col in ['name', 'grade', 'style', 'area']):
                        route_analysis = self._analyze_routes(df, key)
                        route_docs.extend(route_analysis)
            else:
                # Single dataframe
                route_analysis = self._analyze_routes(climb_data, 'climb_data')
                route_docs.extend(route_analysis)
        
        if not route_docs:
            # Create minimal fallback
            route_docs.append(Document(
                page_content="No specific route data available from datasets",
                metadata={'source': 'system'}
            ))
        
        print(f"Created route vectorstore with {len(route_docs)} documents")
        return Chroma.from_documents(route_docs, self.embeddings)
    
    def _analyze_routes(self, df, source_name):
        """Analyze route characteristics"""
        docs = []
        
        # Analyze various route characteristics
        for col in ['style', 'type', 'area', 'rock_type', 'length']:
            if col in df.columns:
                value_counts = df[col].value_counts()
                for value, count in value_counts.head(15).items():
                    if pd.notna(value):
                        text = f"Route {col.title()} Analysis - {source_name}: {value} appears in {count} routes ({count/len(df)*100:.1f}%)"
                        docs.append(Document(
                            page_content=text,
                            metadata={col: value, 'count': count, 'source': source_name}
                        ))
        
        return docs
    
    def create_injury_prevention_vectorstore(self, gym_data, sheets_data):
        """Create injury prevention knowledge from datasets"""
        
        injury_docs = []
        
        # Extract injury prevention info from gym data
        if gym_data is not None:
            # Look for exercises related to injury prevention
            prevention_keywords = ['stretch', 'mobility', 'warm', 'cool', 'recovery', 'rehab', 'prevention']
            
            for _, row in gym_data.iterrows():
                try:
                    title = str(row.get('Title', '')).lower()
                    desc = str(row.get('Desc', '')).lower()
                    
                    if any(keyword in title or keyword in desc for keyword in prevention_keywords):
                        text = f"Injury Prevention Exercise: {row.get('Title', 'Unknown')}"
                        if pd.notna(row.get('Desc', '')):
                            text += f", Description: {row.get('Desc', '')}"
                        if pd.notna(row.get('BodyPart', '')):
                            text += f", Target: {row.get('BodyPart', '')}"
                        
                        injury_docs.append(Document(
                            page_content=text,
                            metadata=row.to_dict()
                        ))
                except Exception as e:
                    continue
        
        # Extract injury prevention info from sheets
        if sheets_data is not None:
            injury_cols = [col for col in sheets_data.columns if any(keyword in col.lower() 
                          for keyword in ['injury', 'prevention', 'safety', 'warm', 'cool', 'recovery'])]
            
            for _, row in sheets_data.iterrows():
                try:
                    for col in injury_cols:
                        value = row.get(col, '')
                        if pd.notna(value) and str(value).strip():
                            injury_docs.append(Document(
                                page_content=f"{col}: {value}",
                                metadata={'column': col, 'source': 'google_sheets'}
                            ))
                except Exception as e:
                    continue
        
        if not injury_docs:
            # Create minimal fallback
            injury_docs.append(Document(
                page_content="No specific injury prevention data available from datasets",
                metadata={'source': 'system'}
            ))
        
        print(f"Created injury prevention vectorstore with {len(injury_docs)} documents")
        return Chroma.from_documents(injury_docs, self.embeddings)
    
    def create_workout_in_db(self, workout_request: str) -> str:
        """
        Parse a user request for creating a workout and POST it to the database.
        
        Args:
            workout_request: Natural language description of the workout to create
            
        Returns:
            JSON string with the created workout or error message
        """
        try:
            # Use LLM to parse the workout request into structured data
            parse_prompt = f"""
            Parse the following workout request into a structured JSON format.
            The JSON should have this structure:
            {{
                "name": "workout name",
                "description": "brief description",
                "userId": null,
                "scheduledDate": "ISO 8601 date string (YYYY-MM-DDTHH:MM:SS.sssZ) or null if not specified",
                "exercises": [
                    {{
                        "name": "exercise name",
                        "sets": number,
                        "reps": number or null,
                        "duration": duration in seconds or null,
                        "rest": rest time in seconds or null
                    }}
                ]
            }}
            
            Date parsing rules:
            - If a specific date is mentioned (e.g., "October 10, 2025", "tomorrow", "next Monday"), convert it to ISO 8601 format
            - If no date is mentioned, set scheduledDate to null
            - Today's date is October 10, 2025
            - Use UTC timezone for the date
            
            Workout request: {workout_request}
            
            Return ONLY the JSON, no other text.
            """
            
            # Get structured workout data from LLM
            workout_json_str = self.llm(parse_prompt)
            
            # Clean up the response to ensure it's valid JSON
            workout_json_str = workout_json_str.strip()
            if workout_json_str.startswith("```json"):
                workout_json_str = workout_json_str[7:]
            if workout_json_str.startswith("```"):
                workout_json_str = workout_json_str[3:]
            if workout_json_str.endswith("```"):
                workout_json_str = workout_json_str[:-3]
            workout_json_str = workout_json_str.strip()
            
            workout_data = json.loads(workout_json_str)
            
            # POST to the API endpoint
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
                error_data = response.json()
                return json.dumps({
                    "success": False,
                    "error": error_data.get("error", "Failed to create workout"),
                    "status_code": response.status_code
                }, indent=2)
                
        except json.JSONDecodeError as e:
            return json.dumps({
                "success": False,
                "error": f"Failed to parse workout data: {str(e)}",
                "raw_response": workout_json_str if 'workout_json_str' in locals() else None
            }, indent=2)
        except requests.RequestException as e:
            return json.dumps({
                "success": False,
                "error": f"API request failed: {str(e)}"
            }, indent=2)
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }, indent=2)
    
    def setup_agents(self):
        """Create specialized agents for different coaching aspects"""
        
        # Exercise Prescription Agent
        exercise_qa = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.exercise_vectorstore.as_retriever(search_kwargs={"k": 8}),
            chain_type="stuff"
        )
        
        # Progression Planning Agent
        progression_qa = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.progression_vectorstore.as_retriever(search_kwargs={"k": 5}),
            chain_type="stuff"
        )
        
        # Technique Coach Agent
        technique_qa = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.technique_vectorstore.as_retriever(search_kwargs={"k": 5}),
            chain_type="stuff"
        )
        
        # Injury Prevention Agent
        injury_qa = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.injury_prevention_vectorstore.as_retriever(search_kwargs={"k": 4}),
            chain_type="stuff"
        )
        
        # Route Analysis Agent
        route_qa = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.route_vectorstore.as_retriever(search_kwargs={"k": 4}),
            chain_type="stuff"
        )
        
        # Define tools for the coordinator agent
        tools = [
            Tool(
                name="Exercise_Prescription",
                func=exercise_qa.run,
                description="Recommend specific exercises and training protocols from comprehensive gym exercise database"
            ),
            Tool(
                name="Progression_Planning", 
                func=progression_qa.run,
                description="Plan grade progressions and timelines based on climbing performance data"
            ),
            Tool(
                name="Technique_Coaching",
                func=technique_qa.run,
                description="Provide technique advice and movement tips from climbing training data"
            ),
            Tool(
                name="Injury_Prevention",
                func=injury_qa.run,
                description="Provide safety and injury prevention advice from exercise and training databases"
            ),
            Tool(
                name="Route_Analysis",
                func=route_qa.run,
                description="Analyze routes and provide climbing strategy advice based on route database"
            ),
            Tool(
                name="Create_Workout",
                func=self.create_workout_in_db,
                description="""Creates and saves a workout to the database. Use this when the user wants to CREATE and SAVE a workout.
                Input: A clear description of the workout including workout name, exercises with sets/reps/duration, and optionally a scheduled date.
                Example input: 'Create a workout called "Finger Strength" scheduled for October 15, 2025 with hangboard training: 5 sets of 10 second hangs with 3 minute rest'
                The tool will parse the request and save it to the database, returning confirmation."""
            )
        ]
        
        # Coordinator Agent that orchestrates other agents
        self.coordinator = initialize_agent(
            tools,
            self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            max_iterations=6
        )
    
    def create_training_plan(self, user_query: str) -> str:
        """Main interface for creating training plans"""
        
        enhanced_query = f"""
        As an expert climbing coach with access to comprehensive datasets and tools, respond to: {user_query}
        
        Your available tools:
        - Create_Workout: Creates and saves workouts to database (use when user wants to create/save a workout)
        - Exercise_Prescription: Recommends exercises from 2900+ exercise database
        - Progression_Planning: Plans grade progressions using climbing data
        - Technique_Coaching: Provides technique advice from training data
        - Injury_Prevention: Provides safety and injury prevention advice
        - Route_Analysis: Analyzes routes and provides climbing strategies
        
        IMPORTANT: When using Create_Workout, pass the entire workout description as input.
        Example: If user says "Create a workout called X with exercises Y", 
        use Create_Workout with input: "Create a workout called X with exercises Y"
        
        Analyze the user's request and use appropriate tools to provide a comprehensive, data-driven response.
        """
        
        return self.coordinator.run(enhanced_query)
    
    def analyze_dataset_stats(self):
        """Print statistics about loaded datasets"""
        print("\n=== Dataset Statistics ===")
        
        try:
            print(f"Exercise vectorstore: {self.exercise_vectorstore._collection.count()} documents")
        except:
            print("Exercise vectorstore: Unable to get count")
        
        try:
            print(f"Progression vectorstore: {self.progression_vectorstore._collection.count()} documents")
        except:
            print("Progression vectorstore: Unable to get count")
            
        try:
            print(f"Route vectorstore: {self.route_vectorstore._collection.count()} documents")
        except:
            print("Route vectorstore: Unable to get count")
        
        try:
            print(f"Technique vectorstore: {self.technique_vectorstore._collection.count()} documents")
        except:
            print("Technique vectorstore: Unable to get count")
        
        try:
            print(f"Injury prevention vectorstore: {self.injury_prevention_vectorstore._collection.count()} documents")
        except:
            print("Injury prevention vectorstore: Unable to get count")

# Usage example with actual dataset paths
if __name__ == "__main__":
    # Initialize with your dataset paths
    coach = ClimbingCoachSystem(
        kaggle_gym_path="gym_exercise_data.csv",  # Path to downloaded Kaggle gym dataset
        kaggle_climb_path="climb_dataset.csv",    # Path to downloaded Kaggle climb dataset
        google_sheets_url="https://docs.google.com/spreadsheets/d/1J6d45EqIlIsIqNdi2X-Zl-EGFxf9d9T3R_W55xrpEAs/export?format=csv&gid=1650492946"
    )
    
    # Print dataset statistics
    coach.analyze_dataset_stats()
    
    # Example queries
    queries = [
        "Create a workout called 'V5 Power Training' scheduled for October 15, 2025 with campus board ladders: 4 sets of 6 rungs with 3 minute rest, and hangboard repeaters: 6 sets of 7 seconds with 3 seconds off",
        "Create a 6-week plan for a V3 climber aiming to reach V5",
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        print("="*70)
        response = coach.create_training_plan(query)
        print(response)
        print("\n" + "="*70 + "\n")