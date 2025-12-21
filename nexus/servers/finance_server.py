from mcp.server.fastmcp import FastMCP
from nexus.servers.tools import get_technical_summary, get_market_news

# Initialize the Server
mcp = FastMCP("Nexus Finance")

@mcp.tool()
def analyze_stock(ticker: str) -> dict:
    """
    Returns deterministic technical indicators (RSI, SMA) for a stock.
    Use this to get the 'Math' view of the market.
    """
    return get_technical_summary(ticker)

@mcp.tool()
def search_news(query: str) -> list[dict]:
    """
    Searches for recent market news.
    Use this to find 'Fundamental' reasons (Lawsuits, Earnings, Hype).
    """
    return get_market_news(query)

if __name__ == "__main__":
    mcp.run()