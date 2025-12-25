from mcp.server.fastmcp import FastMCP

# Import from the sibling 'tools.py' module
# We use a try/except block to handle running as script vs module
try:
    from nexus.servers.tools import get_technical_summary, get_company_info, get_market_news
except ImportError:
    # Fallback if running directly inside the folder
    from tools import get_technical_summary, get_company_info, get_market_news

mcp = FastMCP("AlphaCouncil Finance")

@mcp.tool()
def analyze_stock(ticker: str) -> str:
    """Returns RSI, SMA, and price action."""
    return get_technical_summary(ticker)

@mcp.tool()
def get_fundamentals(ticker: str) -> str:
    """Returns P/E, Margins, and Debt."""
    return get_company_info(ticker)

@mcp.tool()
def search_news(query: str) -> str:
    """Returns recent news headlines."""
    return get_market_news(query)

if __name__ == "__main__":
    mcp.run()