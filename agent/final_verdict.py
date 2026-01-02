# agent/final_verdict.py
from agent.state import AgentState

def get_weights(style: str, risk: str):
    """
    Returns weight dictionary based on User Style and Risk Tolerance.
    """
    style = style.lower().strip()
    risk = risk.lower().strip()

    # --- TRADER LOGIC (Technicals lead) ---
    if style == "trader":
        if risk == "aggressive":
            return {"tech": 0.60, "fund": 0.10, "risk": 0.30}
        elif risk == "conservative":
            return {"tech": 0.40, "fund": 0.20, "risk": 0.40}
        else: # Moderate (Default)
            return {"tech": 0.50, "fund": 0.20, "risk": 0.30}

    # --- INVESTOR LOGIC (Fundamentals lead) ---
    elif style == "investor":
        if risk == "aggressive":
            return {"tech": 0.10, "fund": 0.60, "risk": 0.30}
        elif risk == "conservative":
            return {"tech": 0.10, "fund": 0.40, "risk": 0.50}
        else: # Moderate (Default)
            return {"tech": 0.20, "fund": 0.50, "risk": 0.30}
    
    # Fallback
    return {"tech": 0.33, "fund": 0.33, "risk": 0.34}

def calculate_verdict(state: AgentState) -> dict:
    # 1. Get Weights
    user_style = state.get("user_style", "investor")
    risk_profile = state.get("risk_profile", "moderate")
    weights = get_weights(user_style, risk_profile)
    
    # 2. Get Scores (Safely)
    def clean_score(val):
        try:
            return float(val)
        except (ValueError, TypeError):
            return 50.0

    tech_score = clean_score(state.get("tech_confidence_final"))
    fund_score = clean_score(state.get("fund_confidence_final"))
    risk_danger = clean_score(state.get("risk_danger_score"))

    # ✅ 3. THE NEW FORMULA: Convert Danger to Safety
    # If risk_danger is 0, safety is 100. If risk_danger is 100, safety is 0.
    safety_score = 100.0 - risk_danger

    weighted_score = (
        (tech_score * weights["tech"]) + 
        (fund_score * weights["fund"]) + 
        (safety_score * weights["risk"])
    )
    
    # ✅ 4. NORMALIZED THRESHOLDS
    # Now that the max score is 100, we can use standard percentages:
    if weighted_score >= 70: 
        signal = "BUY"
    elif weighted_score <= 40:
        signal = "SELL"
    else:
        signal = "HOLD"

    # 5. Generate Explanation
    explanation = (
        f"Confidence Score: {weighted_score:.1f}%. "
        f"(Tech: {tech_score}, Fund: {fund_score}, Safety: {safety_score}). "
        f"Profile: {user_style}/{risk_profile}."
    )

    return {
       "final_signal": signal,
       "final_confidence": round(weighted_score, 1),
       "final_explanation": explanation
    }