from typing import List, Dict
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from .state import Graph_state
from dotenv import load_dotenv
load_dotenv()

# Initialize your LLM client
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
)

ROUTER_SYSTEM_PROMPT = """
You are the **Central Dispatcher AI**, the routing core of a multi-agent AI interview platform.
Your only job is to analyze the current application state and deterministically
choose the correct next agent to activate.

##  YOUR PURPOSE
You are given a snapshot of the current system state and must decide which AI agent should act next. Your decision must be based ONLY on the provided state and the rules below. Your output must be a single line containing exactly one valid agent name.

## ⚙️ AVAILABLE AGENTS & ROLES
- user_object_agent: Extracts structured user data (skills, experience, etc.) from the uploaded resume. Only runs once, at the beginning.
- question_maker_agent: Generates interview questions for the selected `interview_type` based on the user's profile. Runs once per interview round.
- question_asker_agent: Asks the next question in the sequence from `question_list`.
- answer_verifier_agent: Evaluates the user's answer and provides verdict and feedback.
- general_talking_agent: Answers general queries about the platform, welcomes users, and provides guidance.

## 📦 STATE SNAPSHOT
You are given the following fields:
user_object: {user_object}
interview_type: {interview_type}
question_list: {question_list}
current_question_index: {current_question_index}
current_phase: {current_phase}
current_user_query: {current_user_query}




## 🔁 ROUTING DECISION LOGIC 

Apply the following rules in order. Return the most appropriate matching agent **only**.

1. **Missing or Incomplete User Object**
   - Condition: `user_object` is `null`  , or does not contain essential fields like `"skills"` or `"projects"`.
   - Action: `user_object_agent`
2. **No Questions Generated**
   - Condition: `user_object` exists, an `interview_type` is selected, but `question_list` is `null` or `[]`.
   - Action: `question_maker_agent`

You are also provided with the previous chat history , In case of confusion refer to the chat history , as it can 
hint to which agent to route 


3. **User Answer Needs Evaluation**
   - Action: `answer_verifier_agent`

4. **Ask Next Interview Question**
   - Action: `question_asker_agent`

5. **No Active Interview Yet**
   - Action: `general_talking_agent`

6. **Fallback (Catch-All)**
   - Condition: If none of the above conditions apply
   - Action: `general_talking_agent`



## ⚠️ STRICT OUTPUT RULE
Your entire response **must** be a single line of lowercase plain text:
-  Correct: `user_object_agent`
-  Incorrect: `"user_object_agent"`
-  Incorrect: `The next agent is user_object_agent.`
-  Incorrect: ` "agent": "user_object_agent" `
-  Incorrect: user_object_agent⏎ (with newline or spaces)


Use this data to decide routing using the logic above. Return only the name of the selected agent, nothing else.

"""


def Router(state: Graph_state) -> Graph_state:
    """
    Router to determine which agent should handle the query.
    Includes chat history to provide context for routing decisions.
    """
    user_object = state.get("user_object", None)
    interview_type = state.get("interview_type", None)
    question_list = state.get("question_list", None)
    current_question_index = state.get("current_question_index", None)
    current_phase = state.get("current_phase", None)
    current_user_query = state.get("current_user_query", "")

    prompt_text = ROUTER_SYSTEM_PROMPT.format(
        user_object=user_object,
        interview_type=interview_type,
        question_list=question_list,
        current_question_index=current_question_index,
        current_phase=current_phase,
        current_user_query=current_user_query,
       
    )

    
    messages = [SystemMessage(content=prompt_text)]

    
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            messages.append(HumanMessage(content=msg.content))
        elif isinstance(msg, AIMessage):
            messages.append(AIMessage(content=msg.content))

    # Add current user query as the last HumanMessage
    #messages.append(HumanMessage(content=query))   
    # already done in initialisation step 

    # Call LLM to get the chosen agent
    response = llm.invoke(messages)
    agent_name = response.content.strip().lower()



    # Validate agent name, fallback to human_in_loop
    valid_agents = {
        "user_object_agent",
        "question_maker_agent",
        "question_asker_agent",
        "answer_verifier_agent",
        "general_talking_agent"
    }

    if agent_name not in valid_agents:
        agent_name = "general_talking_agent"  # fallback for safety
    state["messages"].append(AIMessage(content=agent_name))

    # Update active_agent in state
    state["active_agent"] = agent_name

    return state



