from typing import Callable, Dict, Any

class ToolRegistry:
    """
    A framework-agnostic registry for tools.
    This allows us to test tools without running an MCP server.
    """
    def __init__(self):
        self._tools: Dict[str, Callable] = {}

    def register(self, name: str):
        """Decorator to register a function as a tool."""
        def decorator(func: Callable):
            self._tools[name] = func
            return func
        return decorator

    def call(self, name: str, **kwargs) -> Any:
        """Executes a tool by name with arguments."""
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not found.")
        
        try:
            return self._tools[name](**kwargs)
        except Exception as e:
            return {"error": str(e), "status": "failed"}

    def list_tools(self):
        return list(self._tools.keys())

# Global instance
registry = ToolRegistry()