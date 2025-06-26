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

QUESTION_ASKER_PROMPT = """
You are the **QuestionAskerBot**, an intelligent AI interviewer responsible for drivinga structured interview based on a predefined list of questions.You must follow strict flow control and coordinate with the answer_verifier_agent by asking the correct question at the correct time.

## PURPOSE
Your job is to ask either:
- the next primary question from the interview's `question_list`, or
- a follow-up question if instructed by the answer_verifier_agent.

The interview consists of multiple questions, which may include max 2  follow-up questions per main question.

## INPUTS GIVEN
- `question_list`: A list of questions to be asked, including follow-up questions.
- `current_question_index`: The index of the current question in the `question_list`.
- `feedback`: Feedback provided by the answer_verifier_agent, which may contain follow-up instructions.
- `feedback_reason`: A detailed explanation of the feedback provided by the answer_verifier_agent.



## RULES
1. **Follow-up Detection**:
   - If `feedback_reason` contains a meaningful follow-up instruction, ask that follow-up instead of the main question.
   - Do NOT increment the `current_question_index`.

2. **Main Question Transition**:
   - If no follow-up is needed , ask the question at `question_list[current_question_index]` 
   - dont Increment the `current_question_index it will be done by the code logic `.

3. **End of Interview**:
   - If `current_question_index >= len(question_list)`, end the interview with a closing statement and set `current_phase` to `"summary"`.
## INPUTS GIVEN 
## OUTPUT FORMAT
Only output the next question to be asked. No extra explanation. Be professional and ask like a real interviewer is asking a question.

given inputs :
question_list : {question_list}
index : {index}
feedback : {feedback}
feedback_reason : {feedback_reason}
user_query : {user_query}

You are also provided with the chat history for refernce 
"""


def question_asker_agent(state : Graph_state)->Graph_state:
    user_query = state["current_user_query"]
    question_list = state.get("question_list", [])
    index = state.get("current_question_index", 0)
    feedback = state.get("feedback", "")
    feedback_reason = state.get("feedback_reason", "")

    if index >= len(question_list):
        state["final_response"] = "Thank you for your answers. That concludes the interview. We'll now summarize your performance."
        state["current_phase"] = "summary"
        state["active_agent"] = "question_asker_agent"
        state["messages"].append(AIMessage(content=state["final_response"]))
        return state

    full_prompt = QUESTION_ASKER_PROMPT.format(
        question_list=question_list,
        index=index,
        feedback=feedback
        ,feedback_reason=feedback_reason
        
    )

    messages = [SystemMessage(content=full_prompt)]

    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            messages.append(HumanMessage(content=msg.content))
        elif isinstance(msg, AIMessage):
            messages.append(AIMessage(content=msg.content))
    
    response = llm.invoke(messages)

    assistant_reply = response.content.strip()

    # Update the state with assistant reply
    state["messages"].append(AIMessage(content=assistant_reply)) 
    state["final_response"] = assistant_reply
    state["active_agent"] = "question_asker_agent"
    state["current_phase"] = "question asked go for evaluation"

    return state


