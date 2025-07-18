from typing import List, Dict
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from .state import Graph_state
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
import json
load_dotenv()

# Initialize your LLM client
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
)

class AnswerAnalysisResult(BaseModel):
    reasoning: str = Field(" A brief, one-sentence explanation of your evaluation")
    verdict: str = Field("Either 'sufficient' or 'needs_follow_up'")
    feedback: str = Field("Instruction for the question asker agent to ask the next question")


ANSWER_VERIFIER_SYSTEM_PROMT = """
# ROLE & GOAL
You are the **Answer Verifier Agent**, an expert AI acting as a senior technical hiring manager.
 Your role is to meticulously evaluate a candidate's answer to a specific interview question. You must determine
 if the answer is sufficient or if a follow-up question is necessary to probe for deeper understanding.

# CONTEXT & INPUTS

You will be provided with the following information for your evaluation:
- `question_asked`: The exact question that the candidate was asked.
- `candidate_answer`: The candidate's verbatim response.
- the chat history of the interveiw

here are the inputs :
question_asked : {question_asked}
candidate_answer : {candidate_answer}

You MUST follow these steps in order to make a fair and consistent evaluation:

**Step 1: Analyze Answer Quality.**
- Compare the `candidate_answer` directly against the `question_asked`.
- Assess the answer based on these criteria:
  - **Depth & Detail:** Did the candidate provide specifics, examples, or metrics, or was the answer superficial and high-level?
  - **Relevance & Accuracy:** Was the answer on-topic and technically correct?
  - **Clarity:** Was the explanation clear and easy to understand?

**Step 2: Make a Primary Decision.**
- Based on your analysis, make an initial `verdict`. Choose one:
  - `"sufficient"`: The candidate demonstrated solid understanding and answered the question fully.
  - `"needs_follow_up"`: The answer was weak, incomplete, ambiguous, or raises further questions that need clarification.
  - You have been provided the interview history for reference , Note you can only return follow up question as a verdict ,
  once per main question , if you have already done so , you need to return sufficient

**Step 3: Apply the Follow-up Rule.**
- This is a critical logic check.
- **IF** your primary decision was `"needs_follow_up"` **AND** you have ot asked for followup question: for the current main question
  - Your final `verdict` remains `"needs_follow_up"`.
  - You MUST generate a concise `feedback_for_asker` string, guiding the QuestionAskerBot on what to probe next. (e.g., "Ask for a specific example of the trade-off they mentioned.")
- **ELSE** (This means the answer was sufficient OR the follow-up limit  has been reached):
  - Your final `verdict` MUST be `"sufficient"`. This ensures the interview moves forward.
  - The `feedback_for_asker` should be a simple "Proceed with the next main question."


# 📝 OUTPUT SPECIFICATION

{format_instructions}

## Example 1: Follow-up Needed

  "reasoning": "The candidate described the 'what' but not the 'why' of their architectural choice.",
  "verdict": "needs_follow_up",
  "feedback": "Ask the candidate to elaborate on the specific reasons behind choosing Pinecone over other vector stores for that project."

"""

def answer_verifier_agent(state: Graph_state)->Graph_state:
    """
    Evaluates the user's answer and provides verdict and feedback.
    """
    interview_type = state.get("interview_type", "Porjects and skills")
    user_object = state.get("user_object", None)
    question_list = state.get("question_list", None)
    feedback_list = state.get("feedback_list", None)
    current_question_index = state.get("current_question_index", 0)
    current_user_query = state.get("current_user_query", "")

    print("Answer Verifier Agent")
    print(question_list)
    print(current_question_index)

    question_asked = question_list[current_question_index]
    print(question_asked)
    candidate_answer = current_user_query
    print(candidate_answer)
    parser = JsonOutputParser(pydantic_object=AnswerAnalysisResult)

    full_prompt = ANSWER_VERIFIER_SYSTEM_PROMT.format(
        question_asked=question_asked,
        candidate_answer=candidate_answer,
        format_instructions=parser.get_format_instructions()
    )

    messages = [HumanMessage(content = full_prompt)]

    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            messages.append(HumanMessage(content=msg.content))
        elif isinstance(msg, AIMessage):
            messages.append(AIMessage(content=msg.content))

    chain = llm | parser

    result = {}

    try:
        # The 'result' will be a Python dictionary, not a string
        result = chain.invoke(messages)
        print("Successfully Parsed Result::", result)
    except Exception as e:
        # Catch potential parsing errors from the chain
        print(f"Error parsing LLM response: {e}")
        result = {
            "reasoning": "Failed to parse LLM output.",
            "verdict": "sufficient", # Default to sufficient to move on
            "feedback": "There was a parsing error. Proceeding to the next question."
        }

      # implement feedback count tooo store them for the user in the list

    if result["verdict"] == "sufficient":
        state["current_question_index"] += 1
    # ----------------------

    feedback_list = state.get("feedback_list", []) # Safely get the list
    feedback_list.append(result) # Append the whole result for better history

    state["feedback_list"] = feedback_list
    state["feedback"] = result["feedback"]

    # It's good practice to store all parts of the feedback
    state["previous_question"] = question_asked
    state["previous_feedback"] = result

    state["current_phase"] = "questioning" # This should probably be 'questioning' to go back to the asking agent
    state["active_agent"] = "answer_verifier_agent"
    state["final_response"] = result["feedback"]

    state["messages"].append(AIMessage(content=f"Evaluation: {result}"))

    return state










