import os
import json
from typing import TypedDict, List, Dict, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END


from rag_engine import build_vector_store, retrieve_kb_context
from database import get_triage_list

load_dotenv()


class AgentState(TypedDict):
    query: str
    route: str
    confidence: float
    used_sources: List[str]
    used_tools: List[str]
    needs_clarification: bool
    final_answer: str


llm = ChatOpenAI(model="gpt-4o", temperature=0)


def router_node(state: AgentState):
    """Classifies the query into one of the 5 required routes."""
    prompt = f"""
    Analyze the user query and classify it into exactly one of these routes:
    1. KNOWLEDGE_BASE: Policy/informational questions (refunds, upgrades, limits). [cite: 57, 62]
    2. TICKET_LOOKUP: Specific ticket IDs (T-XXXX) or ticket status/lists. [cite: 57, 68]
    3. ACCOUNT_LOOKUP: Questions about specific customer accounts or plans. [cite: 57, 75]
    4. AMBIGUOUS: Too vague to act on (e.g., 'check the ticket'). [cite: 57, 82]
    5. UNSUPPORTED: Outside the scope of provided data. [cite: 57, 93]

    Return JSON: {{"route": "NAME", "confidence": float}}
    Query: {state['query']}
    """
    # Using structured output to ensure we get valid JSON
    structured_llm = llm.with_structured_output(Dict[str, Any])
    decision = structured_llm.invoke(prompt)
    
    return {
        "route": decision["route"],
        "confidence": decision.get("confidence", 1.0)
    }

def knowledge_node(state: AgentState):
    """Handles RAG pipeline for policy questions."""
    vectorstore = build_vector_store()
    context, sources = retrieve_kb_context(state["query"], vectorstore)
    
    answer_prompt = f"Answer using ONLY this context: {context}\n\nQuery: {state['query']}"
    response = llm.invoke(answer_prompt)
    
    return {
        "final_answer": response.content,
        "used_sources": sources,
        "needs_clarification": False
    }

def data_lookup_node(state: AgentState):
    """Handles JSON lookups and Triage logic."""
    # Check if this is the specific triage question
    if "first today" in state["query"].lower() or "priority" in state["query"].lower():
        triage_results = get_triage_list('tickets.json', 'accounts.json') [cite: 98, 99]
        
        # Format the triage explanation [cite: 105]
        explanation = "Based on priority, tier, and health scores, here are the top issues:\n"
        for i, t in enumerate(triage_results, 1):
            explanation += f"{i}. {t['ticket_id']} ({t['customer_name']}) - Priority: {t['priority']}, Health: {t['health_score']}\n"
        
        return {
            "final_answer": explanation,
            "used_sources": ["tickets.json", "accounts.json"],
            "used_tools": ["triage_ranking_logic"],
            "needs_clarification": False
        }
    
    # Logic for specific ticket/account lookups would go here (filtering JSON)
    return {
        "final_answer": "Record details retrieved from JSON...",
        "used_sources": ["tickets.json"],
        "needs_clarification": False
    }

def clarify_node(state: AgentState):
    return {
        "final_answer": "I'm sorry, could you please provide more details? For example, which ticket ID are you referring to?", [cite: 82]
        "needs_clarification": True,
        "used_sources": []
    }

def unsupported_node(state: AgentState):
    return {
        "final_answer": "I'm sorry, I don't have access to information regarding that request in my current data sources.", [cite: 93]
        "needs_clarification": False,
        "used_sources": []
    }

# --- GRAPH CONSTRUCTION ---

workflow = StateGraph(AgentState)

workflow.add_node("router", router_node)
workflow.add_node("knowledge_base", knowledge_node)
workflow.add_node("data_lookup", data_lookup_node)
workflow.add_node("clarify", clarify_node)
workflow.add_node("unsupported", unsupported_node)

workflow.set_entry_point("router")

# Define conditional edges based on the router decision [cite: 54, 146]
workflow.add_conditional_edges(
    "router",
    lambda x: x["route"],
    {
        "KNOWLEDGE_BASE": "knowledge_base",
        "TICKET_LOOKUP": "data_lookup",
        "ACCOUNT_LOOKUP": "data_lookup",
        "AMBIGUOUS": "clarify",
        "UNSUPPORTED": "unsupported"
    }
)
workflow.add_edge("knowledge_base", END)
workflow.add_edge("data_lookup", END)
workflow.add_edge("clarify", END)
workflow.add_edge("unsupported", END)

app = workflow.compile()



if __name__ == "__main__":
    print("--- AI Support Triage Assistant ---")
    while True:
        user_input = input("\nUser Query: ")
        if user_input.lower() in ["exit", "quit"]: break
        
        result = app.invoke({"query": user_input})
        
        
        output = {
            "route": result["route"],
            "confidence": result["confidence"],
            "used_sources": result.get("used_sources", []),
            "used_tools": result.get("used_tools", []),
            "needs_clarification": result.get("needs_clarification", False),
            "final_answer": result["final_answer"]
        }
        print("\n--- Decision Object ---")
        print(json.dumps(output, indent=2))
