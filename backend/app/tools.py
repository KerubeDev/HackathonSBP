"""Pluggable execution tools. New business capabilities should implement this protocol."""
from typing import Protocol, Any
class AnalysisTool(Protocol):
    name: str
    def run(self, payload: dict[str, Any]) -> dict[str, Any]: ...
class ToolRegistry:
    def __init__(self): self._tools: dict[str, AnalysisTool] = {}
    def register(self, tool: AnalysisTool) -> None: self._tools[tool.name] = tool
    def get(self, name: str) -> AnalysisTool: return self._tools[name]
    def names(self) -> list[str]: return sorted(self._tools)
registry = ToolRegistry()
