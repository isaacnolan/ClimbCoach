#!/usr/bin/env python3
"""
Test script for the Claude agent workout creation functionality.

This script demonstrates how the ClimbingCoachSystem can now:
1. Parse natural language workout requests
2. Structure them into the correct format
3. POST them to the database via the API endpoint

Prerequisites:
- The SvelteKit dev server must be running (npm run dev)
- The database must be set up with the correct schema
- Environment variables must be configured (OPENAI_API_KEY)
"""

from claude_agent_flow import ClimbingCoachSystem

def test_workout_creation():
    """Test creating workouts through the agent"""
    
    # Initialize the coach system
    # The default API URL is http://localhost:5173
    # Adjust if your dev server is on a different port
    coach = ClimbingCoachSystem(api_base_url="http://localhost:5173")
    
    # Example workout creation requests
    workout_requests = [
        "Create a workout called 'Beginner Hangboard' scheduled for October 10, 2025 with the following exercises: "
        "Hangboard jugs for 3 sets of 15 seconds with 2 minute rest, "
        "and core planks for 3 sets of 30 seconds",
        
        "Create a workout named 'Campus Board Power' for tomorrow with campus laddering for 4 sets of 6 rungs "
        "with 3 minute rest between sets",
        
        "Make a new workout called 'Antagonist Training' scheduled for next Monday with push-ups for 3 sets of 12 reps "
        "with 90 second rest, and dips for 3 sets of 10 reps with 90 second rest",
        
        "Create a workout called 'Quick Session' with hangboard for 3 sets of 10 seconds (no date specified)"
    ]
    
    print("=" * 80)
    print("TESTING WORKOUT CREATION VIA CLAUDE AGENT")
    print("=" * 80)
    
    for i, request in enumerate(workout_requests, 1):
        print(f"\n\nTest {i}:")
        print(f"Request: {request}")
        print("-" * 80)
        
        try:
            response = coach.create_training_plan(request)
            print(f"Response:\n{response}")
        except Exception as e:
            print(f"Error: {str(e)}")
        
        print("-" * 80)

def test_direct_workout_creation():
    """Test the create_workout_in_db method directly"""
    
    coach = ClimbingCoachSystem(api_base_url="http://localhost:5173")
    
    print("\n\n" + "=" * 80)
    print("TESTING DIRECT WORKOUT CREATION METHOD")
    print("=" * 80)
    
    workout_request = (
        "Create a workout called 'V5 Power Endurance' scheduled for October 15, 2025 with the following exercises: "
        "4x4 bouldering (4 routes, 4 sets) with 2 minute rest, "
        "hangboard repeaters for 6 sets of 7 seconds on with 3 seconds off for 6 reps, "
        "and lock-off training for 3 sets of 5 reps per arm"
    )
    
    print(f"\nRequest: {workout_request}")
    print("-" * 80)
    
    try:
        result = coach.create_workout_in_db(workout_request)
        print(f"Result:\n{result}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    print("-" * 80)

if __name__ == "__main__":
    print("\nNOTE: Make sure your SvelteKit dev server is running on http://localhost:5173")
    print("Run 'npm run dev' in another terminal if it's not already running.\n")
    
    # Uncomment the test you want to run:
    
    # Test via the agent coordinator (uses all agent tools)
    test_workout_creation()
    
    # Test the workout creation method directly
    # test_direct_workout_creation()
