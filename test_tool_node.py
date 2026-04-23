from typing import TypedDict, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
import os
from dotenv import load_dotenv

load_dotenv()

# ------------------------------
# 1. 定义 State（对应图里的 State）
# ------------------------------
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

# ------------------------------
# 2. 定义 Node（对应图里的两个 Node）
# ------------------------------

# Node 1: Agent（和用户交互，判断下一步去哪）
def agent_node(state: AgentState):
    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("API_KEY"),
        base_url="https://api.deepseek.com/v1"
    )
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

# Node 2: Tool（模拟获取电费估算）
def energy_cost_tool(state: AgentState):
    # 这里模拟工具调用，返回一个固定的估算结果
    tool_response = AIMessage(content="根据你的情况，你的月均电费大约是 200 元。")
    return {"messages": [tool_response]}

# ------------------------------
# 3. 定义 Edge（条件路由，对应图里的 Where to go）
# ------------------------------
def where_to_go(state: AgentState):
    """根据最后一条消息，判断下一步去哪：
    - 如果 Agent 提到了「需要调用电费估算工具」，就去 Tool 节点
    - 否则直接结束对话
    """
    last_message = state["messages"][-1].content.lower()
    # Let's make the condition more flexible to test the tool
    if "电费" in last_message or "energy cost" in last_message or "electricity" in last_message or "bill" in last_message:
        return "call_tool"  # 去工具节点
    return "end"  # 结束

# ------------------------------
# 4. 构建 Graph
# ------------------------------
workflow = StateGraph(AgentState)

# 添加节点
workflow.add_node("agent", agent_node)
workflow.add_node("energy_cost_tool", energy_cost_tool)

# 设置入口
workflow.set_entry_point("agent")

# 添加条件边（对应图里的分支）
workflow.add_conditional_edges(
    "agent",
    where_to_go,
    {
        "call_tool": "energy_cost_tool",
        "end": END
    }
)

# 工具节点执行完后，回到 Agent 节点（对应图里的循环）
workflow.add_edge("energy_cost_tool", "agent")

# 编译图
graph = workflow.compile()

# ------------------------------
# 5. 运行示例
# ------------------------------
if __name__ == "__main__":
    print("=== Test 1: Original message ===")
    # 初始用户输入（对应图里的 human 消息）
    initial_state = {
        "messages": [
            HumanMessage(content="what are solar panels? and how much can I save on electricity bills?")
        ]
    }

    # 执行图
    for output in graph.stream(initial_state):
        for key, value in output.items():
            print(f"--- Node: {key} ---")
            for msg in value["messages"]:
                print(f"{msg.type}: {msg.content[:100]}...\n" if len(msg.content) > 100 else f"{msg.type}: {msg.content}\n")
    
    print("\n=== Test 2: Chinese message to trigger tool ===")
    # Test with Chinese message that should trigger the tool
    initial_state_chinese = {
        "messages": [
            HumanMessage(content="我想知道我的电费情况")
        ]
    }

    # 执行图
    for output in graph.stream(initial_state_chinese):
        for key, value in output.items():
            print(f"--- Node: {key} ---")
            for msg in value["messages"]:
                print(f"{msg.type}: {msg.content}\n")