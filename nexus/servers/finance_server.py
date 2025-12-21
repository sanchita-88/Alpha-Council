from mcp.server.fastmcp import FastMCP
from nexus.servers.tools import get_technical_summary, get_market_news, get_company_info

# Initialize the Server
mcp = FastMCP("Nexus Finance")

@mcp.tool()
def analyze_stock(ticker: str) -> dict:
    """
    Technical Analysis: Returns RSI, SMA, and price action.
    Use for: Timing, Trends, Momentum.
    """
    return get_technical_summary(ticker)

@mcp.tool()
def search_news(query: str) -> list[dict]:
    """
    Risk Analysis: Searches for recent news, lawsuits, and macro events.
    Use for: Sentiment, External Risks.
    """
    return get_market_news(query)

@mcp.tool()
def get_fundamentals(ticker: str) -> dict:
    """
    Fundamental Analysis: Returns P/E, Market Cap, Sector, and Financials.
    Use for: Valuation, Long-term viability.
    """
    return get_company_info(ticker)

if __name__ == "__main__":
    mcp.run()