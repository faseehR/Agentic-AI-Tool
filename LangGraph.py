fimport os
import json
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

class AgentState(TypedDict):
    query: str
    route: str
    confidence: float
    used_sources: List[str]
    final_answer: str

def router_node(state: AgentState):
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    return {"route": "TICKET_LOOKUP", "confidence": 0.9} 


def knowledge_node(state: AgentState):
    return {"final_answer": "Retrieved answer here...", "used_sources": ["refund_policy.md"]}


workflow = StateGraph(AgentState)
workflow.add_node("router", router_node)
workflow.add_node("knowledge_base", knowledge_node)


workflow.set_entry_point("router")
workflow.add_conditional_edges(
    "router",
    lambda x: x["route"],
    {
        "KNOWLEDGE_BASE": "knowledge_base",
        "TICKET_LOOKUP": "data_lookup", 
        "AMBIGUOUS": "clarify_node",    
        
    }
)

app = workflow.compile()
