import json
import re
from typing import Dict, Any, List, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage

from app.backend.llm import get_llm
from app.backend.prompts import SYSTEM_PROMPTS, DIAGNOSIS_PROMPT, TRANSLATION_DICT

# Define the Graph State
class AgentState(TypedDict):
    messages: List[BaseMessage]
    language: str                  # 'en', 'hi', 'kn'
    patient_info: Dict[str, Any]    # extracted age, gender, symptoms, duration, severity
    triage_summary: str            # medical advice and summary in local language
    suggested_specialty: str       # proposed doctor specialty
    triage_stage: str              # 'GATHERING', 'DIAGNOSED', 'REFERRED'
    referral_required: bool
    # Credentials and configuration
    provider: str
    api_key: str
    model_name: str

def parse_extracted_json(text: str) -> Dict[str, Any]:
    """Helper to parse JSON out of LLM response, handling markdown blocks."""
    # Find JSON block if it's wrapped in markdown
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        # Fallback to finding the first { and last }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            json_str = text[start:end+1]
        else:
            json_str = text
            
    try:
        return json.loads(json_str)
    except Exception:
        # Fallback if parsing fails
        return {
            "age": None,
            "gender": None,
            "symptoms": None,
            "duration": None,
            "severity": "Low",
            "triage_summary": "",
            "suggested_specialty": "General Physician",
            "referral_required": False
        }

# --- Nodes ---

def triage_node(state: AgentState) -> Dict[str, Any]:
    """
    Triage Agent: Conversations with the patient in their selected language.
    Gathers symptoms, age, gender, duration, severity.
    """
    messages = state["messages"]
    lang = state.get("language", "en")
    
    # Retrieve model instance
    try:
        llm = get_llm(
            provider=state["provider"],
            api_key=state["api_key"],
            model_name=state["model_name"]
        )
    except Exception as e:
        # If there's an error building LLM (e.g. invalid key), append an error message
        error_msg = f"System Error: {str(e)}"
        return {"messages": messages + [AIMessage(content=error_msg)]}
        
    system_prompt = SYSTEM_PROMPTS.get(lang, SYSTEM_PROMPTS["en"])
    
    # Format messages for LangChain
    formatted_messages = [SystemMessage(content=system_prompt)] + messages
    
    response = llm.invoke(formatted_messages)
    
    return {"messages": messages + [response]}

def evaluation_node(state: AgentState) -> Dict[str, Any]:
    """
    Evaluation Node: Analyzes conversation history to extract details
    and determine if triaging is complete or if an emergency was detected.
    """
    messages = state["messages"]
    lang = state.get("language", "en")
    language_full = TRANSLATION_DICT.get(lang, "English")
    
    # Render messages for the evaluator
    history_str = ""
    for m in messages:
        sender = "Patient" if isinstance(m, HumanMessage) else "Assistant"
        history_str += f"{sender}: {m.content}\n"
        
    eval_prompt = DIAGNOSIS_PROMPT.format(history=history_str, language_full=language_full)
    
    try:
        llm = get_llm(
            provider=state["provider"],
            api_key=state["api_key"],
            model_name=state["model_name"]
        )
        eval_response = llm.invoke([HumanMessage(content=eval_prompt)])
        data = parse_extracted_json(eval_response.content)
    except Exception:
        # Fallback in case of errors
        data = {
            "age": None,
            "gender": None,
            "symptoms": None,
            "duration": None,
            "severity": "Low",
            "triage_summary": "",
            "suggested_specialty": "General Physician",
            "referral_required": False
        }
        
    # Check if we should move to DIAGNOSED stage.
    # We move to DIAGNOSED if:
    # 1. Severity is High (requires immediate attention, no further gathering needed)
    # 2. Or, we successfully collected symptoms, duration, age, and severity.
    current_stage = state.get("triage_stage", "GATHERING")
    
    if current_stage == "GATHERING":
        has_essential_info = (
            data.get("age") is not None and 
            data.get("gender") is not None and 
            data.get("symptoms") is not None and 
            data.get("duration") is not None
        )
        is_high_severity = data.get("severity") == "High"
        
        if is_high_severity or has_essential_info:
            current_stage = "DIAGNOSED"
            
    patient_info = {
        "age": data.get("age"),
        "gender": data.get("gender"),
        "symptoms": data.get("symptoms"),
        "duration": data.get("duration"),
        "severity": data.get("severity", "Low")
    }
    
    return {
        "patient_info": patient_info,
        "triage_summary": data.get("triage_summary", ""),
        "suggested_specialty": data.get("suggested_specialty", "General Physician"),
        "referral_required": data.get("referral_required", False),
        "triage_stage": current_stage
    }

# --- Router ---
def route_next(state: AgentState) -> Literal["triage", "__end__"]:
    """Determines whether to keep triaging or finish."""
    # If the stage is DIAGNOSED or REFERRED, we end this LangGraph pass
    if state.get("triage_stage") in ["DIAGNOSED", "REFERRED"]:
        return "__end__"
    return "triage"

# --- Build the Graph ---
def build_agent_graph():
    builder = StateGraph(AgentState)
    
    # Add nodes
    builder.add_node("triage", triage_node)
    builder.add_node("evaluate", evaluation_node)
    
    # Set entry point
    builder.set_entry_point("triage")
    
    # Connect nodes
    builder.add_edge("triage", "evaluate")
    
    # Add conditional router after evaluate
    builder.add_conditional_edges(
        "evaluate",
        route_next,
        {
            "triage": "triage",
            "__end__": END
        }
    )
    
    return builder.compile()

# Instantiate compiled graph
agent_graph = build_agent_graph()
