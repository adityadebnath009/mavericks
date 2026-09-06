from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

@dataclass
class AgentResult:
    agent_name: str
    status: str
    data: Dict[str, Any]
    
    latency_ms: Optional[float] = None
    execution_mode: Optional[str] = None
    confidence: Optional[float] = None

    sources: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
