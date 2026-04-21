from typing import TypedDict, Literal

# --------------------------
# 状态定义
# --------------------------
class TravelState(TypedDict):
    user_input: dict
    recommended_dest: str
    budget_info: dict
    itinerary: str
    user_feedback: Literal["可以", "不可以", None]
    plan_index: int  # 0=肇庆, 1=惠州, 2=清远

# --------------------------
# 三套完全不同目的地行程
# --------------------------
DESTINATIONS = ["肇庆鼎湖山+七星岩", "惠州西湖+双月湾", "清远漂流+英西峰林"]

PLAN_TEMPLATES = [
    # 方案1：肇庆
"""
【{dest} 3日行程】
Day1: 广州→肇庆→七星岩（喀斯特湖光）→住端州区
Day2: 鼎湖山（森林氧吧+飞水潭）→岩前村慢逛
Day3: 宋城墙+包公祠→返程

预算明细：
交通 300 + 住宿 550
餐饮 320 + 景点 230
总计：1400 元｜剩余：100 元
""",
    # 方案2：惠州
"""
【{dest} 3日行程】
Day1: 广州→惠州西湖→水东街古街→住惠城
Day2: 双月湾海景+海龟湾→住海边民宿
Day3: 罗浮山登山+客家菜→返程

预算明细：
交通 320 + 住宿 500
餐饮 350 + 景点 230
总计：1400 元｜剩余：100 元
""",
    # 方案3：清远
"""
【{dest} 3日行程】
Day1: 广州→古龙峡漂流→黄腾峡→住清城区
Day2: 英西峰林骑行（广东小桂林）→住英德
Day3: 连州地下河（溶洞暗河）→返程

预算明细：
交通 330 + 住宿 520
餐饮 340 + 景点 210
总计：1400 元｜剩余：100 元
"""
]

# --------------------------
# 节点函数
# --------------------------
def input_node(state: TravelState) -> TravelState:
    print("📥 【用户输入节点】")
    preferred_dest = input("目的地（广州周边）：") or "广州周边"
    budget = int(input("总预算（元）：") or 1500)
    days = int(input("天数：") or 3)
    user_input = {
        "preferred_dest": preferred_dest,
        "budget": budget,
        "days": days,
        "interests": ["自然风光"]
    }
    print(f"✅ 用户输入：{user_input}")
    return {"user_input": user_input, "plan_index": 0}

def recommend_dest_node(state: TravelState) -> TravelState:
    print("\n🗺️ 【目的地推荐节点】")
    idx = state["plan_index"] % 3
    dest = DESTINATIONS[idx]
    print(f"✅ 推荐目的地：{dest}")
    return {"recommended_dest": dest}

def calculate_budget_node(state: TravelState) -> TravelState:
    print("\n💰 【预算计算节点】")
    budget_info = {
        "total_budget": 1500,
        "transport": 300 + state["plan_index"] * 20,
        "hotel": 550 - state["plan_index"] * 50,
        "food": 320 + state["plan_index"] * 20,
        "attractions": 230 - state["plan_index"] * 20,
        "remaining": 100
    }
    total = budget_info["transport"]+budget_info["hotel"]+budget_info["food"]+budget_info["attractions"]
    print(f"✅ 总计：{total} 元｜剩余：100 元")
    return {"budget_info": budget_info}

def generate_itinerary_node(state: TravelState) -> TravelState:
    print("\n📅 【行程生成节点】")
    idx = state["plan_index"] % 3
    dest = DESTINATIONS[idx]
    itinerary = PLAN_TEMPLATES[idx].format(dest=dest)
    print(itinerary)
    return {
        "itinerary": itinerary,
        "user_feedback": None,
        "plan_index": state["plan_index"] + 1
    }

def user_confirmation_node(state: TravelState) -> TravelState:
    print("\n🙋 【用户确认节点】")
    feedback = input("满意？（可以 / 不可以）：")
    print(f"✅ 用户反馈：{feedback}")
    return {"user_feedback": feedback}

def route_after_confirmation(state: TravelState):
    if state["user_feedback"] == "不可以":
        print("\n🔄 切换下一个目的地，重新生成行程！")
        return "generate_itinerary"
    else:
        print("\n✅ 确认通过，输出最终行程")
        return "output_result"

def output_result_node(state: TravelState):
    print("\n🎉【最终行程】")
    print("="*50)
    print(state["itinerary"])
    print("="*50)
    return {}

# --------------------------
# 构建工作流
# --------------------------
from langgraph.graph import StateGraph, END
workflow = StateGraph(TravelState)

workflow.add_node("user_input", input_node)
workflow.add_node("recommend_dest", recommend_dest_node)
workflow.add_node("calculate_budget", calculate_budget_node)
workflow.add_node("generate_itinerary", generate_itinerary_node)
workflow.add_node("user_confirmation", user_confirmation_node)
workflow.add_node("output_result", output_result_node)

workflow.set_entry_point("user_input")
workflow.add_edge("user_input", "recommend_dest")
workflow.add_edge("recommend_dest", "calculate_budget")
workflow.add_edge("calculate_budget", "generate_itinerary")
workflow.add_edge("generate_itinerary", "user_confirmation")

workflow.add_conditional_edges(
    "user_confirmation",
    route_after_confirmation,
    {
        "generate_itinerary": "generate_itinerary",
        "output_result": "output_result"
    }
)
workflow.add_edge("output_result", END)
app = workflow.compile()

# --------------------------
# 运行
# --------------------------
if __name__ == "__main__":
    print("===== 🚀 LangGraph 三目的地循环演示（1500元）=====")
    print("\n=== Mermaid 流程图 ===")
    print(app.get_graph().draw_mermaid())
    print("\n=== 开始运行 ===")
    app.invoke({})