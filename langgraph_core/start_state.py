import sys
import os
# Adjust the path to your project root accordingly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from typing import Optional, List, Dict
from langchain_core.messages import HumanMessage , AIMessage
from .state import Graph_state
#from backend.db_utils import get_chat_history , get_documents_by_session
from backend.db_utils import get_interview_chat_history , get_interview_session , get_latest_feedback_entry

def initialize_state(user_query: str, session_id: Optional[str] = None) -> Graph_state:
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    raw_history = get_interview_chat_history(session_id)

    formatted_history = []
    for msg in raw_history:
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            formatted_history.append(HumanMessage(content=content))
        elif role == "ai":
            formatted_history.append(AIMessage(content=content))
    #append the user qury 
    formatted_history.append(HumanMessage(content=user_query))

    session_data = get_interview_session(session_id)
    
    if session_data is None:
        session_data = {
            "interview_type": "Project_and_skills",
            "user_object": {},
            "question_list": [],
            "current_question_index": 0,
            "active_agent": ""
        }

   # feedback = get_latest_feedback_entry(session_id)
   # previous_question = feedback["question"] if feedback else None
   # previous_verdict = feedback["verdict"] if feedback else None


    return {
        "session_id": session_id,
        "messages": formatted_history,
        "interview_type": "Project_and_skills",  # fixed for now
        "user_object": session_data["user_object"],                   # to be initialized later using an agent 
        "question_list": session_data["question_list"],  
        "feedback_list": [],              
        "current_question_index": session_data["current_question_index"],
        "current_user_query": user_query,   # curr answer
        "final_response": None,             # can be a question
        "active_agent": "",
        "feedback": None,                       # curr feedback or verdict
        "current_phase": None,  # this will be deicided by the router 
        "previous_question":None,
        "previous_verdict": None
    }
