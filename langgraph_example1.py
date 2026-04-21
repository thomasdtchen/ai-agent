from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# Define state structure
class AgentState(TypedDict):
    messages: list
    user_input: str

# Define node function
def chat_node(state: AgentState):
    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("API_KEY"),
        base_url="https://api.deepseek.com/v1"
    )
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

# Build graph
workflow = StateGraph(AgentState)
workflow.add_node("chat", chat_node)
workflow.set_entry_point("chat")
workflow.add_edge("chat", END)

# Compile and run
app = workflow.compile()
result = app.invoke({"messages": [("user", "Hello!")]})