# Nexus: The Deterministic Financial Engine

**Nexus** is the foundational Model Context Protocol (MCP) server for the Alpha Council autonomous trading system. It acts as the "Body" of the architecture, providing the "Brain" (Agents) with **pure, hallucination-free financial data**.

Unlike standard AI tools that guess or summarize, Nexus executes **deterministic code** to calculate indicators and fetch live market data, ensuring the AI Agents base their decisions on mathematical ground truth.

---

## 🏗 System Architecture

Nexus is built on a **System-First Architecture**, separating tool logic from the transport layer.

| Layer         | Component             | Responsibility |
|---------------|-----------------------|----------------|
| **Interface** | `finance_server.py`   | Exposes tools via FastMCP protocol for Agent consumption. |
| **Registry**  | `servers/registry.py` | Framework-agnostic tool registration (allows testing without a server). |
| **Logic**     | `servers/tools.py`    | The "Heavy Lifting" — fetches data and orchestrates calculations. |
| **Math**      | `indicators/*.py`     | **Pure Python implementations** of RSI and SMA (No libraries, fully unit-tested). |

---

## 🛠 Available Tools

The server exposes three distinct tools, one for each specialized agent in the Alpha Council swarm:

### 1. `get_technical_summary` (For Technical Agent)
* **Purpose:** Provides the mathematical view of price action.
* **Inputs:** Stock Ticker (e.g., "NVDA").
* **Outputs:**
    * **RSI (14):** Calculated using Wilder’s Smoothing Method.
    * **SMA (50):** Trend identification.
    * **Signal:** Deterministic `BUY`/`SELL`/`HOLD` flag based on thresholds (30/70).

### 2. `get_company_info` (For Fundamental Agent)
* **Purpose:** Provides the valuation and health view of the company.
* **Inputs:** Stock Ticker.
* **Outputs:** P/E Ratio, Market Cap, Debt-to-Equity, Profit Margins, Revenue Growth.

### 3. `get_market_news` (For Risk Agent)
* **Purpose:** Provides the external/macro view.
* **Inputs:** Search Query (e.g., "Tesla").
* **Outputs:** Top 3 recent news headlines and snippets from **US-English** sources (filtered to avoid irrelevant region results).

---

## 🚀 Getting Started

### Prerequisites
* Python 3.10+
* Git

### Installation
1.  Navigate to the `nexus` directory:
    ```bash
    cd nexus
    ```
2.  Install the lean dependency set (No heavy AI libraries required):
    ```bash
    pip install -r requirements.txt
    ```

### Running the Server
Start the MCP server to listen for Agent connections:
```bash
python servers/finance_server.py


🧪 Verification & Testing :
Nexus includes a self-contained verification suite. You can test the logic without running the full server.

Run Unit Tests (Prove the Math):

Bash

python tests/test_indicators.py
Test Live Data Fetching (Prove the Wiring):

Bash

# Test Technical Logic
python -c "from servers.tools import registry; print(registry.call('get_technical_summary', ticker='AAPL'))"

# Test News Search
python -c "from servers.tools import registry; print(registry.call('get_market_news', query='Apple'))"

🔒 Security & Determinism Notes
No API Keys Required: All tools utilize public endpoints (Yahoo Finance, DuckDuckGo) or local math.

Zero Hallucination: Indicators are calculated by code, not LLMs.

Region Locking: Search is strictly bound to region='us-en' to ensure relevance for US Markets.

Built for the Alpha Council Project.