import subprocess
import json
import sys
import os

# Command to run your server
SERVER_CMD = [sys.executable, "nexus/servers/finance_server.py"]

def rpc_request(process, method, params=None, req_id=1):
    """Helper to send a JSON-RPC request and wait for the response."""
    request = {
        "jsonrpc": "2.0",
        "id": req_id,
        "method": method
    }
    if params:
        request["params"] = params
    
    # Send
    print(f"\n📤 Sending command: {method}...")
    try:
        process.stdin.write(json.dumps(request) + "\n")
        process.stdin.flush()
    except OSError:
        print("❌ Error: Pipe broken. The server probably crashed.")
        return None
    
    # Read Response
    while True:
        line = process.stdout.readline()
        if not line:
            break
        try:
            data = json.loads(line)
            # FastMCP might send log messages; ignore them, look for our response ID
            if data.get("id") == req_id:
                return data
        except json.JSONDecodeError:
            continue # Ignore debug text that isn't JSON
    return None

def run_full_test():
    print("🚀 Launching Nexus MCP Server...")

    # FIX 1: Set PYTHONPATH so the server finds the 'nexus' folder
    my_env = os.environ.copy()
    my_env["PYTHONPATH"] = os.getcwd()
    
    # FIX 2: Force UTF-8 encoding to prevent Windows crash on emojis/fancy quotes
    # We also enable PYTHONIOENCODING in the env to be safe
    my_env["PYTHONIOENCODING"] = "utf-8"

    process = subprocess.Popen(
        SERVER_CMD,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding='utf-8',  # <--- CRITICAL FIX FOR WINDOWS
        bufsize=0,
        env=my_env 
    )

    try:
        # 1. Handshake (Initialize)
        init_params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "tester", "version": "1.0"}
        }
        resp = rpc_request(process, "initialize", init_params, req_id=1)
        if not resp:
            raise Exception("Handshake failed")
        print("✅ Handshake Complete.")

        # 2. List Tools (See what is available)
        resp = rpc_request(process, "tools/list", req_id=2)
        if not resp:
            raise Exception("Listing tools failed")
            
        tools = resp['result']['tools']
        tool_names = [t['name'] for t in tools]
        print(f"✅ Found {len(tools)} tools: {tool_names}")

        # 3. Test Technical Tool
        print("\n🧪 Testing Tool: analyze_stock (NVDA)...")
        resp = rpc_request(process, "tools/call", {
            "name": "analyze_stock",
            "arguments": {"ticker": "NVDA"}
        }, req_id=3)
        content = resp['result']['content'][0]['text']
        print(f"📄 Result: {content[:100]}...") 

        # 4. Test Fundamental Tool
        print("\n🧪 Testing Tool: get_fundamentals (NVDA)...")
        resp = rpc_request(process, "tools/call", {
            "name": "get_fundamentals",
            "arguments": {"ticker": "NVDA"}
        }, req_id=4)
        content = resp['result']['content'][0]['text']
        print(f"📄 Result: {content[:100]}...")

        # 5. Test Risk Tool (Search)
        print("\n🧪 Testing Tool: search_news (Tesla)...")
        resp = rpc_request(process, "tools/call", {
            "name": "search_news",
            "arguments": {"query": "Tesla"}
        }, req_id=5)
        content = resp['result']['content'][0]['text']
        print(f"📄 Result: {content[:100]}...")

        print("\n🎉 ALL SYSTEMS GO: The MCP Server is fully functional.")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        # Use simple read() here to avoid decoding errors in stderr too
        print("Server Error Log:")
        print(process.stderr.read())
    
    finally:
        process.kill()

if __name__ == "__main__":
    run_full_test()