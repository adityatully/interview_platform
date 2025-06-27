from typing import List, Dict
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from .state import Graph_state
import json
import re
from dotenv import load_dotenv
# from rich import print
load_dotenv()


# Initialize your LLM client
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.7,
)


QUESTION_MAKER_PROMPT = """
You are "InteR-ViewBot," an expert AI agent acting as a seasoned hiring manager and technical architect. Your primary function is to generate a set of insightful, deeply technical, and situationally relevant interview questions. You must meticulously analyze the provided candidate information and interview context to craft questions that accurately assess the candidate's depth of knowledge and practical skills.

here are the given inputs

# INPUTS
interview_type:{interview_type}
user_object: {user_object}
# CORE METHODOLOGY
Follow this process step-by-step:
1.  **Deconstruct Inputs:** Carefully parse the interview_type and the user_object given to you in the input
. Identify the candidate's core skills, technologies they've used, specific project achievements (look for metrics and impact), and years of experience.
2.  **Identify Probing Areas:** Pinpoint the most significant or recent technologies listed. For example, if "RAG," "LangChain," or "CrewAI" are mentioned, these are high-priority areas.
3.  **Activate Web Search (Crucial):** You MUST use your web search tool when:
    *   A technology is very recent (e.g., released in the last 2-3 years).
    *   The candidate claims experience with "state-of-the-art" techniques.
    *   You need to understand the current best practices, common challenges, or recent updates for a specific framework or tool mentioned.
    *   **Example of effective search:** If the resume lists "CrewAI," do not just ask "What is CrewAI?". A better approach is to search for "common challenges in CrewAI agent collaboration" or "CrewAI vs AutoGen" and then formulate a question like, "In your CrewAI project, how did you handle state management and ensure consistent communication between agents, especially when dealing with complex, multi-step tasks?"
4.  **Synthesize & Formulate Questions:** Generate questions that probe for deeper understanding. Adhere to these principles:
    *   **Go Beyond Definitions:** Avoid simple "What is X?" questions. Focus on "How," "Why," "Compare/Contrast," "Design," and "What if" scenarios.
    *   **Connect to Experience:** Frame questions around the candidate's listed projects. Instead of "Tell me about vector databases," ask "On project X, you used Pinecone. What were the trade-offs you considered when choosing it over other vector stores like ChromaDB or Weaviate, especially concerning scalability and metadata filtering?"
    *   **Assess Problem-Solving:** Pose a hypothetical problem related to their skills. "Imagine you need to build a system to reduce LLM hallucination in a customer-facing chatbot. Based on your experience with RAG, what specific strategies would you implement and how would you measure their effectiveness?"
    *   **Vary Difficulty:** Include a mix of questions that test fundamental knowledge, practical application, and architectural design thinking.

# INPUTS
- **Interview Type:**  (e.g., "Technical Screening," "Behavioral," "System Design," "AI/ML Deep Dive")
- **User Object:**  (A JSON object containing the candidate's resume data, like `skills: ["Python", "PyTorch", "CrewAI"]`, `projects: [{{"name": "...", "description": "...", "tech_stack": [...]}}]`, etc.)

# CONSTRAINTS & RULES


1.  The number of questions must be between 5 and 10.
2.  The questions must be directly relevant to the `{interview_type}` and the candidate's specific skills and projects. Avoid generic questions if specific information is available.
3.  Do not include any introductory or concluding text, explanations, or conversational filler.
4.  The final output MUST be a valid list in format - ["question1", "question2" ...].

# OUTPUT SPECIFICATION
- Return ONLY a list object containing questions as instructed.
- DO NOT include markdown formatting, code blocks, or any other text outside the list structure. Or i will KILL YOU.
"""


def list_parser(question_list: list[str]):
    out = []

    for line in question_list:
        if line.lstrip()[0] == ("\""):
            out.append(line)

    return out

def question_maker_agent(state : Graph_state)->Graph_state:
    """ generates 10 questons and appends it ot the question list """
    user_object = state.get("user_object", None)
    #print("user_object")
    #print(user_object)
    interview_type = state.get("interview_type", None) # always fixed for now
    #print(interview_type)
    user_object_json_str = json.dumps(user_object, indent=2)
    full_prompt = QUESTION_MAKER_PROMPT.format(
        interview_type = interview_type,
        user_object = user_object_json_str
    )
    messages = [HumanMessage(content=full_prompt)]
    # chat history dosent need to be passed
    #print(messages)
    response = llm.invoke(messages)

    content = response.content.strip()

    #print(content)
    #print(type(content))

    question_list = list_parser(content.split("\n"))
    print("Question List::", question_list)
    # raw_json_str = re.match(r"\{(.|\s)*\}", content)
    # print("Raw JSON String::", raw_json_str)
    # raw_json_str = re.sub(r"```$", "", content)
    # print("Raw JSON String::", raw_json_str)

    # print("Raw JSON String::", raw_json_str)
    # print("Raw JSON String::", type(raw_json_str))
    # print("regex ::", raw_json_str.group() if raw_json_str else "No match found")

    questions = question_list
    # if raw_json_str:
    #     question_data = json.loads(raw_json_str.group())
    #     questions = question_data.get("questions", [])

    #     print(question_data)
    #     print(questions)


    if not questions:
        questions = []
        state["final_response"] = "Failed to generate interview questions. Please try again."
    else:
        state["final_response"] = "Generated personalized interview questions."


    state["question_list"] = questions
    state["current_question_index"] = 0
    state["current_phase"] = "questioning"  # for the next phase
    state["active_agent"] = "question_maker_agent"

    print("Question Maker Agent::", state)

    return state