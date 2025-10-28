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
    def __init__(self, api_base_url: str = "http://localhost:5173"):
        self.llm = OpenAI(temperature=0.7)
        self.embeddings = OpenAIEmbeddings()
        self.api_base_url = api_base_url
        self.setup_knowledge_bases()
        self.setup_agents()
    
    def setup_knowledge_bases(self):
        """Create specialized knowledge bases for different climbing domains"""
        
        # 1. Exercise Database (adapted from your gym data)
        self.exercise_vectorstore = self.create_exercise_vectorstore()
        
        # 2. Climbing Grades & Progression
        self.progression_vectorstore = self.create_progression_vectorstore()
        
        # 3. Technique & Skills
        self.technique_vectorstore = self.create_technique_vectorstore()
        
        # 4. Injury Prevention
        self.injury_prevention_vectorstore = self.create_injury_prevention_vectorstore()
    
    def create_exercise_vectorstore(self):
        """Convert gym exercises to climbing-relevant exercises"""
        # Load your Kaggle data
        # df = pd.read_csv("gym_exercise_data.csv")
        
        # For demo, using climbing-specific exercises
        climbing_exercises = [
            {
                "exercise": "Campus Board Training",
                "muscle_groups": "Forearms, Fingers, Core",
                "difficulty": "Advanced",
                "description": "Dynamic finger strength training on campus rungs",
                "progression": "Start with static holds, progress to dynamic movements",
                "sets_reps": "3-5 sets of 3-7 rungs"
            },
            {
                "exercise": "Hangboard Training",
                "muscle_groups": "Forearms, Fingers",
                "difficulty": "Intermediate to Advanced",
                "description": "Finger strength training on various hold types",
                "progression": "Start with jugs, progress to smaller edges and pockets",
                "sets_reps": "5-7 sets of 10-15 second hangs"
            },
            {
                "exercise": "Core Stabilization",
                "muscle_groups": "Core, Abs, Obliques",
                "difficulty": "Beginner to Advanced",
                "description": "Various core exercises for climbing stability",
                "progression": "Planks → L-sits → Front levers",
                "sets_reps": "3-4 sets of 30-60 seconds"
            },
            {
                "exercise": "Antagonist Training",
                "muscle_groups": "Triceps, Chest, Upper Back",
                "difficulty": "All levels",
                "description": "Push movements to balance pulling in climbing",
                "progression": "Push-ups → Dips → Ring work",
                "sets_reps": "2-3 sets of 8-15 reps"
            }
        ]
        
        docs = []
        for exercise in climbing_exercises:
            text = f"Exercise: {exercise['exercise']}, Muscles: {exercise['muscle_groups']}, "
            text += f"Difficulty: {exercise['difficulty']}, Description: {exercise['description']}, "
            text += f"Progression: {exercise['progression']}, Sets/Reps: {exercise['sets_reps']}"
            docs.append(Document(page_content=text, metadata=exercise))
        
        return Chroma.from_documents(docs, self.embeddings)
    
    def create_progression_vectorstore(self):
        """Create climbing grade progression knowledge"""
        progression_data = [
            {
                "current_grade": "V3",
                "target_grade": "V5",
                "timeline": "6-12 weeks",
                "focus_areas": "Power endurance, technique refinement, route reading",
                "training_emphasis": "60% technique, 30% strength, 10% endurance"
            },
            {
                "current_grade": "V1",
                "target_grade": "V3",
                "timeline": "4-8 weeks",
                "focus_areas": "Basic technique, finger strength, movement efficiency",
                "training_emphasis": "70% technique, 20% strength, 10% flexibility"
            }
        ]
        
        docs = []
        for prog in progression_data:
            text = f"Progression from {prog['current_grade']} to {prog['target_grade']}: "
            text += f"Timeline: {prog['timeline']}, Focus: {prog['focus_areas']}, "
            text += f"Training emphasis: {prog['training_emphasis']}"
            docs.append(Document(page_content=text, metadata=prog))
        
        return Chroma.from_documents(docs, self.embeddings)
    
    def create_technique_vectorstore(self):
        """Create technique-focused knowledge base"""
        techniques = [
            "Flagging: Use opposite leg to maintain balance during reaches",
            "Drop knee: Lower inside knee to improve reach and reduce strain",
            "Heel hooks: Use heel to pull body closer to wall and reduce arm strain",
            "Toe hooks: Hook toe under holds to maintain position during rests",
            "Mantling: Press down on holds to get on top of them",
            "Stemming: Push off opposing surfaces to maintain position"
        ]
        
        docs = [Document(page_content=tech) for tech in techniques]
        return Chroma.from_documents(docs, self.embeddings)
    
    def create_injury_prevention_vectorstore(self):
        """Create injury prevention knowledge base"""
        injury_prevention = [
            "Warm up with easy climbing and dynamic stretches for 10-15 minutes",
            "Gradual progression: increase training load by no more than 10% per week",
            "Rest days: Take at least 2 full rest days per week",
            "Antagonist training: Balance pulling with pushing exercises",
            "Listen to your body: Sharp pain is a warning sign to stop",
            "Finger injuries: Avoid crimping on small holds when fatigued"
        ]
        
        docs = [Document(page_content=tip) for tip in injury_prevention]
        return Chroma.from_documents(docs, self.embeddings)
    
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
            - Today's date is October 9, 2025
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
            retriever=self.exercise_vectorstore.as_retriever(),
            chain_type="stuff"
        )
        
        # Progression Planning Agent
        progression_qa = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.progression_vectorstore.as_retriever(),
            chain_type="stuff"
        )
        
        # Define tools for the coordinator agent
        tools = [
            Tool(
                name="Exercise_Prescription",
                func=exercise_qa.run,
                description="Use this to recommend specific exercises and training protocols"
            ),
            Tool(
                name="Progression_Planning", 
                func=progression_qa.run,
                description="Use this to plan grade progressions and timelines"
            ),
            Tool(
                name="Create_Workout",
                func=self.create_workout_in_db,
                description="""Use this tool when the user wants to CREATE and SAVE a workout to the database.
                Input should be a clear description of the workout including: workout name, exercises with sets/reps/duration.
                Example: 'Create a hangboard workout called "Finger Strength" with 5 sets of 10 second hangs on medium edges with 3 minute rest'
                This tool will parse the request and save it to the database."""
            )
           
        ]
        
        # Coordinator Agent that orchestrates other agents
        self.coordinator = initialize_agent(
            tools,
            self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )
    
    def create_training_plan(self, user_query: str) -> str:
        """Main interface for creating training plans"""
        
        # Enhanced prompt for coordinator
        enhanced_query = f"""
        As a climbing coach, respond to this user request: {user_query}
        
        Available actions:
        1. If the user wants to CREATE and SAVE a workout to the database, use the Create_Workout tool
        2. If the user wants exercise recommendations, use Exercise_Prescription
        3. If the user wants progression planning, use Progression_Planning
        4. For general training plans, consider all aspects:
           - Appropriate exercises and training protocols
           - Grade progression timeline and milestones  
           - Technique focuses for improvement
           - Injury prevention and safety measures
        
        Analyze the user's intent and use the appropriate tools to provide a comprehensive response.
        """
        
        return self.coordinator.run(enhanced_query)

# Usage example
if __name__ == "__main__":
    coach = ClimbingCoachSystem()
    
    # Example queries
    queries = [
        "Create a workout called 'Finger Strength Foundation' with hangboard training: 5 sets of 10 second hangs with 3 minute rest, and campus board ladders: 4 sets of 5 rungs with 2 minute rest",
        "Create a 6-week plan with specific exercises for a V3 climber aiming to reach V5",
        "Help me improve my finger strength for overhanging routes", 
        "I keep getting pumped on routes, what should I focus on?",
        "Design a weekly training schedule for indoor climbing improvement"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        print("="*50)
        response = coach.create_training_plan(query)
        print(response)
        print("\n" + "="*50 + "\n")