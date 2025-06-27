import sys
import os
# Add the PROJECT folder to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pprint
from langchain_core.messages import AIMessage
from fastapi import FastAPI, File, UploadFile, HTTPException , Form
from pydantic_models import InterviewQueryInput, InterviewQueryResponse
from db_utils import get_interview_chat_history , insert_interview_session , load_full_resume_text , insert_question_feedback , insert_full_resume_text , insert_interview_chat
from langgraph_core.start_state import initialize_state
from langgraph_core.main_graph import the_final_agent
from dotenv import load_dotenv
import uuid
import logging  
import shutil
load_dotenv()

#Opens a file in binary write mode ("wb").
#shutil.copyfileobj(...) copies the uploaded file's contents into the temporary file on disk.

# Set up logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

DEFAULT_MODEL_NAME = "gemini-2.0-flash"

# Initialize FastAPI app
app = FastAPI()


@app.post("/chat", response_model=InterviewQueryResponse) # how to response model 
def chat(query_input:InterviewQueryInput):
    if not query_input.session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    session_id = query_input.session_id
    logging.info(f"Session ID: {session_id}, User Query: {query_input.query}, Model: {DEFAULT_MODEL_NAME}")

    
    chat_history = get_interview_chat_history(session_id)
    # not needed maybe
    state = initialize_state(user_query=query_input.query, session_id=query_input.session_id)
    #pprint.pprint(state)
    
    
    #rag_chain = get_rag_chain(query_input.model.value)
    #answer = rag_chain.invoke({
    #    "input": query_input.question,
    #    "chat_history": chat_history
    #})['answer']  

    final_state = the_final_agent.invoke(state)
   # pprint.pprint(final_state)
    answer = final_state.get("final_response", "No response generated.")
    final_state["messages"].append(AIMessage(content=answer))
    #insert_application_logs(
    #    session_id, query_input.question, final_state["final_response"]
    #)
    #return QueryResponse(answer=final_state["final_response"], session_id=session_id, model=query_input.model)

    insert_interview_session(session_id , final_state["interview_type"] , final_state["user_object"] , final_state["question_list"] , final_state["current_question_index"] , final_state["active_agent"])
    #insert_application_logs(session_id, query_input.question, answer, DEFAULT_MODEL_NAME)
    insert_interview_chat(session_id , query_input.query , answer)
    question_list = final_state.get("question_list", [])
    feedback_list = final_state.get("feedback_list", [])

    #skipping ecuae of dict for now 
    #for question, feedback in zip(question_list, feedback_list):
    #    insert_question_feedback(session_id, question, feedback)
            
    logging.info(f"Session ID: {session_id}, AI Response: {answer}")
    return InterviewQueryResponse(answer=answer, session_id=session_id)


@app.post("/upload-doc")
def upload_and_index_document(
    file: UploadFile = File(...),
    filename: str = Form(...),
    file_type: str = Form(...),
    session_id: str = Form(...)
):
    session_id = session_id 
    allowed_extensions = ['.pdf']
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed types are: {', '.join(allowed_extensions)}")

    temp_file_path = f"temp_{file.filename}" # made a temp file o the local storega to upload the uploade file

    try:
        # Save the uploaded file to a temporary file
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        #file_id = insert_document_record(file.filename , file_type ,  session_id )
        file_id = insert_full_resume_text(temp_file_path, session_id , filename)
        #success = index_document_to_chroma(temp_file_path, file_id)
        #sucesss2 = insert_full_pdf_text(temp_file_path, file_id)
        #print(file_id)
        #print(success)
        #print(sucesss2)

        if file_id:
            return {"message": f"File {file.filename} has been successfully uploaded and indexed.", "file_id": file_id}
        else:
            delete_document_record(file_id)
            raise HTTPException(status_code=500, detail=f"Failed to index {file.filename}.")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

