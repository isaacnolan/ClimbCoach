from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from No_Langchain import ClimbingCoachSystem
import os

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the ClimbingCoachSystem
coach = ClimbingCoachSystem(
    kaggle_gym_path=os.getenv("KAGGLE_GYM_PATH", "data/gym_data.csv"),
    kaggle_climb_path=os.getenv("KAGGLE_CLIMB_PATH", "data/climb_data.csv"),
    google_sheets_url=os.getenv("GOOGLE_SHEETS_URL", ""),
    api_base_url="http://localhost:5173"
)

class ChatRequest(BaseModel):
    message: str

@app.post("/analyze")
async def analyze_performance(chat_request: ChatRequest):
    try:
        # Log incoming request
        print(f"Received request with message: {chat_request.message}")
        
        # Use the proper create_training_plan method that includes all tools and context
        response_text = coach.create_training_plan(chat_request.message)
        print(f"Response: {response_text}")
        
        if not response_text:
            raise ValueError("Empty response from create_training_plan")
            
        return {"reply": response_text, "status": "success"}
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": str(e), "status": "error"}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)