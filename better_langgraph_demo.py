"""
Better LangGraph Demo: Solar Panel Consultation System

This demo showcases why LangGraph is needed for complex AI workflows:
1. Multi-step consultation with branching logic
2. Parallel tool execution for different data sources
3. State management across conversation turns
4. Conditional routing based on user needs
5. Iterative refinement with feedback loops
"""
from typing import TypedDict, Annotated, Sequence, List, Dict, Any
import operator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
import os
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

# ------------------------------
# 1. Enhanced State Definition
# ------------------------------
class ConsultationState(TypedDict):
    """State that tracks the entire consultation process"""
    messages: Annotated[Sequence[BaseMessage], add_messages]




    user_profile: Annotated[Dict[str, Any], lambda x, y: {**x, **y}]  # Merge dictionaries
    analysis_results: Annotated[Dict[str, Any], lambda x, y: {**x, **y}]  # Merge dictionaries
    consultation_stage: Annotated[str, lambda old, new: new]  # Replace with new value
    needs_clarification: Annotated[bool, lambda old, new: new]  # Replace with new value

# ------------------------------
# 2. System Nodes
# ------------------------------

def initial_assessment_node(state: ConsultationState):
    """Initial assessment: Understand user needs and profile"""
    system_prompt = """You are a solar panel consultation expert. Your task is to:
    1. Understand the user's needs and situation
    2. Ask clarifying questions if needed
    3. Determine what information is missing
    4. Guide them to the next appropriate step
    
    Based on the conversation, update the user profile with any information gathered.
    """
    
    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("API_KEY"),
        base_url="https://api.deepseek.com/v1",
        temperature=0.3
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        *state["messages"]
    ]
    
    response = llm.invoke(messages)
    
    # Parse response to extract user information
    content = response.content.lower()
    profile_updates = {}
    
    # Extract potential information from response
    if "location" in content or "address" in content or "city" in content:
        profile_updates["location_mentioned"] = True
    if "bill" in content or "usage" in content or "kwh" in content:
        profile_updates["usage_mentioned"] = True
    if "roof" in content or "shading" in content or "direction" in content:
        profile_updates["roof_mentioned"] = True
    if "budget" in content or "cost" in content or "price" in content:
        profile_updates["budget_mentioned"] = True
    
    # Determine if we need clarification
    needs_clarification = any([
        "what is your" in content,
        "could you tell me" in content,
        "please provide" in content,
        "i need to know" in content,
        "clarify" in content
    ])
    
    return {
        "messages": [response],

        "user_profile": profile_updates,
        "needs_clarification": needs_clarification
    }

def parallel_data_collection_node(state: ConsultationState):
    """Simulate parallel data collection from multiple sources"""
    # Simulate different data collection tools running in parallel
    location_data = {
        "solar_irradiance": "4.5 kWh/m²/day",
        "sunlight_hours": "2800 hours/year",
        "climate_zone": "Temperate"
    }
    
    utility_data = {
        "avg_electricity_rate": "$0.15/kWh",
        "net_metering": "Available (1:1 credit)",
        "incentives": ["Federal Tax Credit (30%)", "State Rebate ($1000)"]
    }
    
    roof_assessment_data = {
        "roof_size": "800 sq ft available",
        "orientation": "South-facing (optimal)",
        "shading": "Minimal shading",
        "roof_condition": "Good (10+ years remaining)"
    }
    
    return {
        "analysis_results": {
            "location_analysis": location_data,
            "utility_analysis": utility_data,
            "roof_assessment": roof_assessment_data,
            "collection_timestamp": datetime.now().isoformat()
        }
    }

def financial_analysis_node(state: ConsultationState):
    """Perform financial analysis based on collected data"""
    user_profile = state.get("user_profile", {})
    analysis_results = state.get("analysis_results", {})
    
    # Simulate financial calculations
    if analysis_results.get("utility_analysis"):
        rate = 0.15  # $/kWh
        avg_monthly_usage = 900  # kWh (default)
        monthly_cost = rate * avg_monthly_usage
        
        # Calculate solar savings
        system_size = 6.0  # kW
        annual_production = system_size * 4.5 * 365  # kWh/year
        annual_savings = annual_production * rate
        
        # System cost and payback
        system_cost = 18000  # $
        after_tax_credit = system_cost * 0.7
        payback_years = after_tax_credit / annual_savings
        
        financial_analysis = {
            "current_monthly_bill": f"${monthly_cost:.2f}",
            "system_size_recommended": f"{system_size} kW",
            "estimated_annual_production": f"{annual_production:.0f} kWh",
            "estimated_annual_savings": f"${annual_savings:.2f}",
            "system_cost": f"${system_cost}",
            "cost_after_incentives": f"${after_tax_credit:.0f}",
            "payback_period": f"{payback_years:.1f} years",
            "lifetime_savings": f"${annual_savings * 25:.0f} (25 years)",
            "recommendation": "Highly recommended - Excellent ROI"
        }
        
        return {
            "analysis_results": {

                "financial_analysis": financial_analysis
            }
        }
    

    return {"analysis_results": {}}

def recommendation_node(state: ConsultationState):
    """Generate personalized recommendations"""
    analysis_results = state.get("analysis_results", {})
    user_profile = state.get("user_profile", {})
    
    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("API_KEY"),
        base_url="https://api.deepseek.com/v1",
        temperature=0.7
    )
    
    # Prepare context for the recommendation
    context = f"""
    Based on the analysis:
    
    Location Analysis: {json.dumps(analysis_results.get('location_analysis', {}), indent=2)}
    Utility Analysis: {json.dumps(analysis_results.get('utility_analysis', {}), indent=2)}
    Roof Assessment: {json.dumps(analysis_results.get('roof_assessment', {}), indent=2)}
    Financial Analysis: {json.dumps(analysis_results.get('financial_analysis', {}), indent=2)}
    
    User Profile: {json.dumps(user_profile, indent=2)}
    
    Generate a comprehensive, personalized recommendation for solar panel installation.
    Include:
    1. System specifications
    2. Financial benefits
    3. Timeline
    4. Next steps
    5. Any caveats or considerations
    """
    
    messages = [
        SystemMessage(content="You are a solar energy consultant providing personalized recommendations."),
        HumanMessage(content=context)
    ]
    
    response = llm.invoke(messages)
    
    return {
        "messages": [response],
        "consultation_stage": "recommendation_generated"
    }

def clarification_node(state: ConsultationState):
    """Handle user clarification requests"""
    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("API_KEY"),
        base_url="https://api.deepseek.com/v1"
    )
    
    messages = [
        SystemMessage(content="The user needs clarification. Ask one specific question to get the missing information needed for accurate solar panel recommendations."),
        *state["messages"][-2:]  # Last couple of messages
    ]
    
    response = llm.invoke(messages)
    
    return {
        "messages": [response],
        "needs_clarification": True
    }

# ------------------------------
# 3. Complex Routing Logic
# ------------------------------

def route_after_assessment(state: ConsultationState):
    """Determine next step after initial assessment"""
    user_profile = state.get("user_profile", {})
    needs_clarification = state.get("needs_clarification", False)
    
    if needs_clarification:
        return "clarification"
    
    # Check if we have enough information to proceed
    has_location = user_profile.get("location_mentioned", False)
    has_usage = user_profile.get("usage_mentioned", False)
    
    if has_location and has_usage:
        return "collect_data"
    else:
        return "clarification"

def route_after_data_collection(state: ConsultationState):
    """Determine next step after data collection"""
    analysis_results = state.get("analysis_results", {})
    
    if "location_analysis" in analysis_results and "utility_analysis" in analysis_results:
        return "financial_analysis"
    else:
        return "collect_data"  # Retry data collection

def route_after_financial_analysis(state: ConsultationState):
    """Determine next step after financial analysis"""
    analysis_results = state.get("analysis_results", {})
    
    if "financial_analysis" in analysis_results:
        return "generate_recommendation"
    else:
        return "financial_analysis"  # Retry analysis

# ------------------------------
# 4. Build the Complex Graph
# ------------------------------

# Create the workflow
workflow = StateGraph(ConsultationState)

# Add all nodes
workflow.add_node("initial_assessment", initial_assessment_node)
workflow.add_node("clarification", clarification_node)
workflow.add_node("collect_data", parallel_data_collection_node)
workflow.add_node("financial_analysis", financial_analysis_node)
workflow.add_node("generate_recommendation", recommendation_node)

# Set entry point
workflow.set_entry_point("initial_assessment")

# Add conditional edges (showcasing complex routing)
workflow.add_conditional_edges(
    "initial_assessment",
    route_after_assessment,
    {
        "clarification": "clarification",
        "collect_data": "collect_data"
    }
)

workflow.add_conditional_edges(
    "clarification",
    lambda state: "initial_assessment",  # Always go back to assessment after clarification
    {"initial_assessment": "initial_assessment"}
)

workflow.add_conditional_edges(
    "collect_data",
    route_after_data_collection,
    {
        "financial_analysis": "financial_analysis",
        "collect_data": "collect_data"  # Loop back if data incomplete
    }
)

workflow.add_conditional_edges(
    "financial_analysis",
    route_after_financial_analysis,
    {
        "generate_recommendation": "generate_recommendation",
        "financial_analysis": "financial_analysis"  # Loop back if analysis fails
    }
)

# Final recommendation ends the workflow
workflow.add_edge("generate_recommendation", END)

# Compile the graph
graph = workflow.compile()

# ------------------------------
# 5. Run the Enhanced Demo
# ------------------------------

def print_state_info(state_key, state_value):
    """Helper to print state information"""
    print(f"\n{'='*60}")
    print(f"STATE UPDATE: {state_key}")
    print(f"{'='*60}")
    
    if state_key == "messages":
        for msg in state_value["messages"]:
            print(f"\n[{msg.type.upper()}]:")
            print(msg.content)
    elif state_key == "user_profile":
        print("User Profile Updated:")
        for key, value in state_value.items():
            print(f"  - {key}: {value}")
    elif state_key == "analysis_results":
        print("Analysis Results:")
        for category, data in state_value.items():
            if category != "collection_timestamp":
                print(f"\n  {category.upper().replace('_', ' ')}:")
                if isinstance(data, dict):
                    for k, v in data.items():
                        print(f"    {k}: {v}")
                else:
                    print(f"    {data}")
    elif state_key == "consultation_stage":
        print(f"Consultation Stage: {state_value}")
    elif state_key == "needs_clarification":
        print(f"Needs Clarification: {state_value}")

if __name__ == "__main__":
    print("\n" + "="*70)
    print("SOLAR PANEL CONSULTATION SYSTEM - LANGGRAPH DEMO")
    print("="*70)
    print("\nThis demo showcases why LangGraph is needed for complex AI workflows:")
    print("1. Multi-step consultation with branching logic")
    print("2. Parallel tool execution for different data sources")
    print("3. State management across conversation turns")
    print("4. Conditional routing based on user needs")
    print("5. Iterative refinement with feedback loops")
    print("\n" + "="*70)
    
    # Initial user query
    initial_state = {
        "messages": [
            HumanMessage(content="I'm interested in solar panels for my home. Can you help me understand if it's worth it and how much I could save?")
        ],
        "user_profile": {},
        "analysis_results": {},
        "consultation_stage": "initial",
        "needs_clarification": False
    }
    
    print("\n💬 INITIAL USER QUERY:")
    print(f"\"{initial_state['messages'][0].content}\"")
    
    print("\n" + "="*70)
    print("STARTING CONSULTATION WORKFLOW...")
    print("="*70)
    
    # Execute the graph
    for i, output in enumerate(graph.stream(initial_state), 1):
        for state_key, state_value in output.items():
            print_state_info(state_key, state_value)
    
    print("\n" + "="*70)
    print("CONSULTATION COMPLETE!")
    print("="*70)
    
    print("\n🎯 WHY LANGGRAPH WAS NEEDED FOR THIS DEMO:")
    print("1. Complex State Management: Tracked user profile, analysis results, and consultation stage")
    print("2. Conditional Routing: Different paths based on available information")
    print("3. Parallel Execution: Multiple data sources collected simultaneously")
    print("4. Feedback Loops: Could loop back for clarification or retry failed steps")
    print("5. Multi-step Workflow: Assessment → Data Collection → Analysis → Recommendation")
    print("\nThis would be very difficult to implement with simple if-else logic or linear chains!")