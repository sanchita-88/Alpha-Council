import json
import sys
import os
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Import your Prompts
from agents.prompts import (
    TECHNICAL_INITIAL_PROMPT,
    FUNDAMENTAL_INITIAL_PROMPT,
    RISK_CRITIQUE_PROMPT
)
from agents.utils import get_current_date

# --- CONFIGURATION ---
# Make sure GROQ_API_KEY is in your .env file!
# agents/nodes.py

def get_llm():
    # UPDATED MODEL NAME below:
    return ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.1)

# --- MCP SERVER CONNECTION ---
# We need to pass the current environment variables + PYTHONPATH
# so the server knows where to find 'nexus.indicators'
env_vars = os.environ.copy()
env_vars["PYTHONPATH"] = os.getcwd()  # This adds D:\alpha-council\Alpha-Council to the path

server_params = StdioServerParameters(
    command=sys.executable, 
    args=["nexus/servers/finance_server.py"], 
    env=env_vars  # <--- CRITICAL CHANGE HERE
)

async def call_mcp_tool(tool_name: str, arguments: dict):
    """Manually calls the MCP server to get data."""
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            # FastMCP returns a list of content, we grab the text
            if result.content and len(result.content) > 0:
                return result.content[0].text
            return "No data returned."

# --- THE AGENT WORKERS ---

async def technical_analyst_node(state):
    """The Technical Analyst Worker"""
    ticker = state["ticker"]
    print(f"\n📈 [Technical Agent] Starting analysis for {ticker}...")
    
    # 1. Get Data from MCP
    try:
        raw_data = await call_mcp_tool("analyze_stock", {"ticker": ticker})
    except Exception as e:
        raw_data = f"Error fetching technical data: {e}"

    # 2. Ask LLM
    llm = get_llm()
    # We format the prompt with the ticker
    system_msg = TECHNICAL_INITIAL_PROMPT.format(ticker=ticker)
    user_msg = f"Here is the live technical data from the tool:\n{raw_data}"
    
    response = await llm.ainvoke([
        SystemMessage(content=system_msg),
        HumanMessage(content=user_msg)
    ])
    
    # 3. Return Result (Parsing logic can be added here or in the graph)
    return {"tech_report": response.content}

async def fundamental_analyst_node(state):
    """The Fundamental Analyst Worker"""
    ticker = state["ticker"]
    print(f"\n💰 [Fundamental Agent] Starting analysis for {ticker}...")
    
    # 1. Get Data from MCP
    try:
        raw_data = await call_mcp_tool("get_fundamentals", {"ticker": ticker})
    except Exception as e:
        raw_data = f"Error fetching fundamental data: {e}"

    # 2. Ask LLM
    llm = get_llm()
    system_msg = FUNDAMENTAL_INITIAL_PROMPT.format(ticker=ticker)
    user_msg = f"Here is the live fundamental data from the tool:\n{raw_data}"

    response = await llm.ainvoke([
        SystemMessage(content=system_msg),
        HumanMessage(content=user_msg)
    ])
    
    return {"fund_report": response.content}

async def risk_analyst_node(state):
    """The Risk Analyst Worker"""
    ticker = state["ticker"]
    # We grab the outputs from the previous agents if they exist
    tech_thesis = state.get("tech_report", "Pending...")
    fund_thesis = state.get("fund_report", "Pending...")
    
    print(f"\n🚨 [Risk Agent] Looking for trouble for {ticker}...")
    
    # 1. Search for bad news via MCP
    try:
        query = f"{ticker} negative news lawsuit fraud earnings miss"
        news_data = await call_mcp_tool("search_news", {"query": query})
    except Exception as e:
        news_data = "No news found or error searching."

    # 2. Formulate Critique using the helper from prompts.py
    from agents.prompts import render_risk_critique_prompt
    
    # Render the prompt dynamically
    prompt = render_risk_critique_prompt(ticker, tech_thesis, fund_thesis)
    
    llm = get_llm()
    response = await llm.ainvoke([
        SystemMessage(content=prompt),
        HumanMessage(content=f"Here are the search results for negative news:\n{news_data}")
    ])
    
    return {"risk_report": response.content}