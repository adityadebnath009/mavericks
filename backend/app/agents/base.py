from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List

from app.agents.context import AgentContext
from app.agents.result import AgentResult

@dataclass
class AgentSpec:
    name: str
    dependencies: List[str] = field(default_factory=list)
    mode_support: List[str] = field(default_factory=list)

class AbstractAgent(ABC):
    @property
    @abstractmethod
    def spec(self) -> AgentSpec:
        """Return the specification for this agent."""
        pass

    @abstractmethod
    async def analyze(self, context: AgentContext) -> AgentResult:
        """Execute the agent's core logic based on the context."""
        pass
