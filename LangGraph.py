from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    query: str
    route: str
    confidence: float
    context: Optional[str]
    used_sources: List[str]
    final_answer: str