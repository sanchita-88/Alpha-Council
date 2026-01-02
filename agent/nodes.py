# agent/nodes.py
import json
import os
import sys
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_path not in sys.path:
    sys.path.append(root_path)
import subprocess
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from agent.state import AgentState
from agent.utils import get_current_date, get_news_cutoff_date
from nexus.servers.tools import get_technical_summary, get_market_news
from agent.prompts import (
    TECHNICAL_INITIAL_PROMPT, TECHNICAL_REBUTTAL_PROMPT,
    FUNDAMENTAL_INITIAL_PROMPT, FUNDAMENTAL_REBUTTAL_PROMPT,
    RISK_CRITIQUE_PROMPT
)

# --- 1. SETUP LLM ---
def get_llm():
    return ChatGroq(model_name="llama-3.1-8b-instant", temperature=0.0)

def call_mcp_tool(tool_name, arguments):
    # 1. Handshake Definitions
    init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "alpha", "version": "1.0"}}}
    init_not = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    tool_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": tool_name, "arguments": arguments}}
    
    payload = json.dumps(init_req) + "\n" + json.dumps(init_not) + "\n" + json.dumps(tool_req) + "\n"

    # 2. Path Resolution
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    server_path = os.path.join(root_dir, "nexus", "servers", "finance_server.py")
    
    # 3. Environment Setup
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([root_dir, os.path.join(root_dir, "nexus")])
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        process = subprocess.Popen(
            [sys.executable, server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            encoding='utf-8',
            bufsize=1
        )
        
        stdout, stderr = process.communicate(input=payload, timeout=15)
        
        if stdout:
            for line in stdout.strip().split("\n"):
                clean_line = line.strip()
                if clean_line.startswith('{"jsonrpc":"2.0"') or clean_line.startswith('{"id":2'):
                    try:
                        resp = json.loads(clean_line)
                        if resp.get("id") == 2:
                            if "result" in resp:
                                return resp["result"]["content"][0]["text"]
                            if "error" in resp:
                                return f"MCP Tool Error: {resp['error']}"
                    except json.JSONDecodeError: 
                        continue

        error_msg = f"Data Fetch Failed. Raw: {stdout[:50]} | Stderr: {stderr[:50]}"
        print(f"❌ [MCP ERROR] {error_msg}")
        return error_msg

    except subprocess.TimeoutExpired:
        process.kill()
        return "Error: MCP Server timed out."
    except Exception as e:
        return f"Execution Failed: {str(e)}"

# --- HELPER: SCORE NORMALIZER ---
def normalize_score(val):
    try:
        f = float(val)
        # ❌ OLD: if f <= 0: return 50.0 
        # ✅ NEW: Allow 0 if the agent finds no risk
        if f < 0: return 0.0 
        
        if 0 < f <= 1.0: return f * 100.0
        if f > 100: return 100.0
        return f
    except:
        # If parsing fails, 50 is a safe "neutral" middle ground
        return 50.0

# --- HELPER: PARSER ---
def parse_json_safely(text):
    try:
        clean = text.replace("```json", "").replace("```", "").strip()
        start = clean.find("{")
        end = clean.rfind("}")
        if start != -1 and end != -1:
            return json.loads(clean[start : end + 1])
        return None
    except:
        return None

# --- 3. AGENT NODES ---

def technical_analyst(state: AgentState):
    ticker = state["ticker"]
    print(f"\n📈 [Technical] Analyzing {ticker}...")
    
    data = call_mcp_tool("analyze_stock", {"ticker": ticker})
    print(f"👀 [DEBUG] Tech Data: {str(data)[:60]}...") 

    llm = get_llm()
    prompt = TECHNICAL_INITIAL_PROMPT.format(ticker=ticker, data=data)
    
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=f"Analyze {ticker} now.")
    ]
    response = llm.invoke(messages)
    
    data_json = parse_json_safely(response.content)
    if data_json:
        conf = normalize_score(data_json.get("confidence", 50))
        thesis = data_json.get("thesis", "Analysis provided.")
    else:
        print(f"⚠️ Tech Parsing Failed. Output: {response.content[:50]}...")
        conf = 50.0
        thesis = response.content

    return {"tech_thesis_initial": thesis, "tech_confidence_initial": conf}

def fundamental_analyst(state: AgentState):
    ticker = state["ticker"]
    print(f"💰 [Fundamental] Analyzing {ticker}...")
    
    data = call_mcp_tool("get_fundamentals", {"ticker": ticker})
    
    llm = get_llm()
    prompt = FUNDAMENTAL_INITIAL_PROMPT.format(ticker=ticker, data=data)
    
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=f"Analyze {ticker} now.")
    ]
    response = llm.invoke(messages)
    
    data_json = parse_json_safely(response.content)
    if data_json:
        conf = normalize_score(data_json.get("confidence", 50))
        thesis = data_json.get("thesis", "Analysis provided.")
    else:
        print(f"⚠️ Fund Parsing Failed. Output: {response.content[:50]}...")
        conf = 50.0
        thesis = response.content

    return {"fund_thesis_initial": thesis, "fund_confidence_initial": conf}


from datetime import datetime, timedelta
from langchain_core.messages import SystemMessage, HumanMessage

def risk_manager(state: AgentState):
    ticker = state["ticker"]
    now = datetime.now()
    current_dt = get_current_date()
    cutoff_dt = get_news_cutoff_date()
    
    # PASS 1: High-Precision Adversarial (SEC/Legal)
    # We keep -GOP and -Somali to avoid the Minnesota noise, but REMOVE -politics
    query_p1 = f"{ticker} stock risk lawsuit investigation fraud SEC DOJ -GOP -Somali"
    news_data = get_market_news(query_p1)

    # PASS 2: SUCCESSIVE RELAXATION (If PASS 1 is empty or weak)
    if not news_data or len(str(news_data)) < 150:
        print(f"⚠️ Precise search empty. Fetching Geopolitical/Trade catalysts...")
        # This will catch the China H200 'export fee' and ByteDance news
        query_p2 = f"{ticker} stock China H200 'export fee' ByteDance order {now.year}"
        news_data = get_market_news(query_p2)

    # PASS 3: Broad Corporate Context (Final Safety Net)
    if not news_data or len(str(news_data)) < 150:
        query_p3 = f"{ticker} stock corporate news risk catalyst {now.strftime('%Y-%m-%d')}"
        news_data = get_market_news(query_p3)

    # ✅ 2. Execute LLM Audit
    llm = get_llm()
    prompt = RISK_CRITIQUE_PROMPT.format(
        ticker=ticker,
        current_date=current_dt,
        news_cutoff_date=cutoff_dt,
        tech_thesis=state.get("tech_thesis_initial", ""),
        fund_thesis=state.get("fund_thesis_initial", ""),
        news=news_data
    )
    
    response = llm.invoke([SystemMessage(content=prompt)])
    data_json = parse_json_safely(response.content)

    # ✅ 3. Persistence Guardrail: Prevent "No News Panic"
    # If the news confirms the H200 export surge, the risk_score should be MODERATE (~40), 
    # and the Tech Confidence should NOT drop to 30.
    risk_score = 0
    if data_json:
        risk_score = normalize_score(data_json.get("risk_score", 0))
        # Logic: If news is actually bullish (like the $14B ByteDance order), 
        # tell the state to maintain technical confidence.
        if "H200" in str(news_data) and "ByteDance" in str(news_data):
            print("💡 News indicates strong China demand. Softening risk impact.")
            risk_score = min(risk_score, 35) 

    return {
        "risk_critique_tech": data_json.get("risk_critique_tech", "None"),
        "risk_critique_fund": data_json.get("risk_critique_fund", "None"),
        "risk_danger_score": risk_score,
        "risk_news_summary": str(news_data)[:500]
    }


def technical_rebuttal(state: AgentState):
    ticker = state["ticker"]
    print(f"📈 [Technical] Rebutting {ticker}...")
    
    # 1. Capture local state variables for the guardrail
    risk_score = int(state.get("risk_danger_score", 0))
    initial_conf = state.get("tech_confidence_initial", 70)
    initial_signal = state.get("tech_signal_initial", "BUY")

    llm = get_llm()
    prompt = TECHNICAL_REBUTTAL_PROMPT.format(
        original_thesis=state.get("tech_thesis_initial", ""),
        risk_score=risk_score,
        risk_critique=state.get("risk_critique_tech", "")
    )
    
    response = llm.invoke([SystemMessage(content=prompt)])
    data_json = parse_json_safely(response.content)
    
    # ✅ PERSISTENCE GUARDRAIL: Prevent "Zero-Confidence Hallucination"
    # If the risk is low (< 30) but the analyst panicked (conf < 20), we force a reset.
    if data_json and data_json.get("final_confidence", 100) < 20 and risk_score < 30:
        print(f"⚠️ Logic Deadlock detected for {ticker}. Overriding LLM panic.")
        data_json["final_confidence"] = initial_conf - 5  # Apply only a minor 'noise' penalty
        data_json["final_signal"] = initial_signal
        data_json["final_thesis"] = f"Maintained initial trend as risk audit ({risk_score}) is non-material."

    if data_json:
        return {
            "tech_thesis_final": data_json.get("final_thesis"), 
            "tech_confidence_final": normalize_score(data_json.get("final_confidence", 50))
        }
        
    return {
        "tech_thesis_final": response.content, 
        "tech_confidence_final": initial_conf
    }

def fundamental_rebuttal(state: AgentState):
    ticker = state["ticker"]
    print(f"💰 [Fundamental] Rebutting {ticker}...")
    
    # 1. Capture baseline state for the guardrail
    risk_score = int(state.get("risk_danger_score", 0))
    initial_conf = state.get("fund_confidence_initial", 60)
    initial_thesis = state.get("fund_thesis_initial", "")

    llm = get_llm()
    prompt = FUNDAMENTAL_REBUTTAL_PROMPT.format(
        original_thesis=initial_thesis,
        risk_score=risk_score,
        risk_critique=state.get("risk_critique_fund", "")
    )
    
    response = llm.invoke([SystemMessage(content=prompt)])
    data_json = parse_json_safely(response.content)
    
    # ✅ PERSISTENCE GUARDRAIL: Prevent Fundamental Panic
    # If risk is baseline (< 30) but the analyst dropped confidence significantly, reset it.
    if data_json and risk_score < 30 and data_json.get("final_confidence", 100) < 40:
        print(f"⚠️ Fundamental Logic Deadlock detected for {ticker}. Stabilizing...")
        data_json["final_confidence"] = initial_conf - 5  # Allow only a minor 'noise' adjustment
        data_json["final_thesis"] = f"Valuation remains robust; audit score ({risk_score}) does not impair core fundamentals."

    if data_json:
        return {
            "fund_thesis_final": data_json.get("final_thesis"), 
            "fund_confidence_final": normalize_score(data_json.get("final_confidence", 50))
        }
        
    return {
        "fund_thesis_final": response.content, 
        "fund_confidence_final": initial_conf
    }

def final_node(state: AgentState):
    print("🏁 [Final Verdict] Math Engine Calculating...")
    from agent.final_verdict import calculate_verdict
    return calculate_verdict(state)