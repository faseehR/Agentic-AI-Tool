from langgraph.graph import StateGraph, END

workflow = StateGraph(AgentState)


workflow.add_node("router", router_function)
workflow.add_node("knowledge_base", rag_function)
workflow.add_node("data_lookup", json_lookup_function)
workflow.add_node("clarify", ambiguity_function)
workflow.add_node("refuse", unsupported_function)


workflow.set_entry_point("router")


workflow.add_conditional_edges(
    "router",
    lambda x: x["route"], 
    {
        "KNOWLEDGE_BASE": "knowledge_base",
        "TICKET_LOOKUP": "data_lookup",
        "ACCOUNT_LOOKUP": "data_lookup",
        "AMBIGUOUS": "clarify",
        "UNSUPPORTED": "refuse"
    }
)


workflow.add_edge("knowledge_base", END)
workflow.add_edge("data_lookup", END)