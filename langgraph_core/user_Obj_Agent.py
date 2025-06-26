import sys
import json
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from .state import Graph_state 
from langchain_core.messages import AIMessage
#from backend.full_db_utils import get_full_pdf_text
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from backend.db_utils import get_resume_text_by_session



llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
)

# The corrected prompt
USER_OBJECT_SYSTEM_PROMPT = """
You are an elite AI-powered Resume Parsing Specialist. Your sole purpose is to meticulously analyze a user's resume text and structure the key information into a **JSON-formatted string**. This string must be perfectly formed so it can be loaded directly into a Python dictionary using `json.loads()`.

## OUTPUT SPECIFICATION & SCHEMA
Your entire response MUST be a single string containing a valid JSON representation of the target dictionary. The schema must include top-level keys: `role`, `skills`, `experience`, and `projects`.
- `role`: (str or null) The user's primary professional role.
- `skills`: (list[str]) A list of technical skills.
- `experience`: (list[dict]) A list of job objects, each with `title`, `company`, `duration`, `responsibilities`.
- `projects`: (list[dict]) A list of project objects, each with `name`, `description`, `technologies_used`.

## CRITICAL RULES
1.  **PYTHON-COMPATIBLE JSON:** Your output must be raw JSON, starting with `{` and ending with `}`. Do not include any explanatory text, comments, or markdown like ` ```json `.
2.  **NO HALLUCINATION:** If information is missing, use JSON `null` or empty lists `[]`.
3.  **ACCURACY:** The data must accurately reflect the resume content.
"""

USER_OBJECT_HUMAN_TEMPLATE = """
Here is the content of the resume. Please process it according to your instructions and provide only the JSON output.

---
Resume Text:
{resume_text}
---
"""


def user_object_agent(state: Graph_state) -> Graph_state:
    user_question = state["current_user_query"]
    session_id = state["session_id"]

    resume_text = get_resume_text_by_session(session_id)
    
    if not resume_text:
        raise ValueError("No resume text found for the given session_id")


    full_prompt = USER_OBJECT_SYSTEM_PROMPT.format(resume_text=resume_text)
    messages = [SystemMessage(content=USER_OBJECT_SYSTEM_PROMPT),HumanMessage(content=USER_OBJECT_HUMAN_TEMPLATE.format(resume_text=resume_text))]


    response = llm.invoke(messages)
    raw_json_str = response.content.strip()
    state["messages"].append(AIMessage(content=response.content))

    try:
        parsed_user_object = json.loads(raw_json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse model response into JSON: {e}")

    state["user_object"] = parsed_user_object
    state["active_agent"] = "user_obj_agent"
    state["final_response"] = "Resume parsed successfully Should we begin the interview??."
    state["current_phase"] = "resume parsing complete"

    return state







    

