from typing import List, Dict
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from .state import Graph_state
import json
import re
from dotenv import load_dotenv
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
- **User Object:**  (A JSON object containing the candidate's resume data, like `skills: ["Python", "PyTorch", "CrewAI"]`, `projects: [{"name": "...", "description": "...", "tech_stack": [...]}]`, etc.)

# CONSTRAINTS & RULES


1.  The number of questions must be between 5 and 10.
2.  The questions must be directly relevant to the `{interview_type}` and the candidate's specific skills and projects. Avoid generic questions if specific information is available.
3.  Do not include any introductory or concluding text, explanations, or conversational filler.
4.  The final output MUST be a valid JSON object.

# OUTPUT SPECIFICATION
Return ONLY a raw JSON object containing a single key, `"questions"`, which holds a list of the generated question strings.

**Example Output Format:**
```json
{{
  "questions": [
    "In your project utilizing the RAG pipeline, how did you approach the chunking strategy for your documents, and what impact did that have on retrieval accuracy?",
    "You list experience with both LangChain and CrewAI. Can you compare and contrast their approaches to defining and managing agentic workflows? When would you choose one over the other?",
    "Describe a time you had to optimize an LLM's inference speed. What specific techniques did you use, and what were the results?",
    "Let's discuss system design. How would you architect a scalable system for fine-tuning a 7B parameter model on a new dataset, assuming you have access to a cloud environment like AWS or GCP?",
    "Your resume mentions improving a recommendation model's performance by 15%. Walk me through the process of identifying the bottleneck and the specific changes you implemented to achieve this uplift."
  ]
}}
```
"""


def question_maker_agent(state : Graph_state)->Graph_state:
    """ generates 10 questons and appends it ot the question list """
    user_object = state.get("user_object", None)
    print(user_object)
    interview_type = state.get("interview_type", None) # always fixed for now 
    print(interview_type)
    user_object_json_str = json.dumps(user_object, indent=2)
    full_prompt = QUESTION_MAKER_PROMPT.format(
        interview_type = interview_type,
        user_object = user_object_json_str
    )
    messages = [SystemMessage(content=full_prompt)]
    # chat history dosent need to be passed 
    print(messages)
    response = llm.invoke(messages)
    content = response.content.strip()

    print(content)

    raw_json_str = re.sub(r"^```(json)?", "", content)
    raw_json_str = re.sub(r"```$", "", content)

    try:
        question_data = json.loads(raw_json_str)
        questions = question_data.get("questions", [])
    except json.JSONDecodeError:
        questions = []
    

    if not questions:
        questions = []
        state["final_response"] = "Failed to generate interview questions. Please try again."
    else:
        state["final_response"] = "Generated personalized interview questions."


    state["question_list"] = questions
    state["current_question_index"] = 0
    state["current_phase"] = "questioning"  # for the next phase 
    state["active_agent"] = "question_maker_agent"

    return state 