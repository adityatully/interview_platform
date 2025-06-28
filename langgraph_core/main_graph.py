from .router_agent import Router
from .state import Graph_state
from .general_agent import general_talking_agent
from .question_asker_agent import question_asker_agent
from .answer_verifier_agent import answer_verifier_agent
from .question_maker_agent import question_maker_agent
from .user_Obj_Agent import user_object_agent
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import add_messages , StateGraph , END
load_dotenv()


main_graph = StateGraph(Graph_state)    
main_graph.add_node("router", Router)
main_graph.add_node("general_talking_agent", general_talking_agent)
main_graph.add_node("question_asker_agent", question_asker_agent)
main_graph.add_node("answer_verifier_agent", answer_verifier_agent)
main_graph.add_node("question_maker_agent", question_maker_agent)
main_graph.add_node("user_object_agent", user_object_agent)
main_graph.set_entry_point("router")


def route_condition(state: Graph_state) -> str:
    return state["active_agent"]  # activ agent


main_graph.add_conditional_edges(
    "router",  
    route_condition,  
    {
        "user_object_agent": "user_object_agent",
        "question_maker_agent": "question_maker_agent",
        "answer_verifier_agent": "answer_verifier_agent",
        "question_asker_agent": "question_asker_agent",
        "general_talking_agent": "general_talking_agent"
    }
)

main_graph.add_edge("general_talking_agent", END)
main_graph.add_edge("question_asker_agent", END)
main_graph.add_edge("user_object_agent" , END)
main_graph.add_edge("question_maker_agent" , "question_asker_agent")

# condtitonal edge if index less than question list go to question asker from answer verifier 

def should_continue_questioning(state: Graph_state) -> str:
    if state["current_question_index"] < len(state["question_list"]):
        return "question_asker_agent"
    else:
        return "general_talking_agent"  # Ends the interview

main_graph.add_conditional_edges(
    "answer_verifier_agent",
    should_continue_questioning,
    {
        "question_asker_agent": "question_asker_agent",
        "general_talking_agent": "general_talking_agent"
    }
)



the_final_agent = main_graph.compile()
