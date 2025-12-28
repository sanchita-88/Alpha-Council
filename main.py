import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Import your graph logic
from agent.graph import app as graph

load_dotenv()

app = FastAPI(title="Rhetora AI Backend")

# Allow Lovable to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# This matches the data Lovable will send
class AnalysisRequest(BaseModel):
    ticker: str
    user_style: str = "investor"
    risk_profile: str = "moderate"

@app.get("/")
def read_root():
    return {"status": "active", "service": "Rhetora Backend"}

@app.post("/analyze")
async def run_analysis(request: AnalysisRequest):
    # Check for API Key
    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(status_code=500, detail="GROQ_API_KEY missing")

    print(f"🔥 Incoming Request: {request.ticker} ({request.user_style}/{request.risk_profile})")

    # Initialize the state EXACTLY how your agents expect it
    initial_state = {
        "ticker": request.ticker,
        "messages": [],
        "user_style": request.user_style,
        "risk_profile": request.risk_profile
    }

    try:
        # Run the Agents
        result = await graph.ainvoke(initial_state)

        # Send the JSON back to Lovable
        return {
            "ticker": request.ticker,
            "final_verdict": {
                "signal": result.get("final_signal", "HOLD"),
                "confidence": result.get("final_confidence", 0),
                "explanation": result.get("final_explanation", "")
            },
            "technical_analysis": {
                "thesis": result.get("tech_thesis_final", ""),
                "confidence": result.get("tech_confidence_final", 0)
            },
            "fundamental_analysis": {
                "thesis": result.get("fund_thesis_final", ""),
                "confidence": result.get("fund_confidence_final", 0)
            },
            "risk_analysis": {
                "score": result.get("risk_danger_score", 0),
                "critique": result.get("risk_critique_tech", "")
            }
        }
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)