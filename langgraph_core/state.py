from typing import TypedDict, Annotated, Optional, List, Dict
from langgraph.graph import add_messages

class Graph_state(TypedDict):
    session_id: str
    messages: List[dict]  # Can be serialized LangChain messages
    interview_type: Optional[str]  # e.g., 'DSA', 'System Design', etc.
    user_object: dict  # Parsed resume fields like name, skills, projects
    question_list: List[str]  # List of generated interview questions
    feedback_list: List[str]  # list of feedback 
    current_question_index: int  # Pointer to current question
    current_user_query: str  # Last message by user query or answer of previous question
    final_response: Optional[str]  # Final AI reply for frontend
    active_agent: str  # e.g., 'dsa_agent', 'design_agent', etc.
    feedback: Optional[str]  # Feedback from answer verifier
    feedback_reason: Optional[str]
    current_phase: Optional[str]  # For flow control
    previous_question: Optional[str]
    previous_feedback: Optional[str]





