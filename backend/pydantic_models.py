from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


# defind structures or models of the data should flow # through the application using Pydantic

#class DocumentInfo(BaseModel):
#    id: int
#    filename: str
#    session_id: str
#    upload_timestamp: datetime
#
#
#class DeleteFileRequest(BaseModel):
#    file_id: int
#







class InterviewQueryInput(BaseModel):
    query: str
    session_id: str



class InterviewQueryResponse(BaseModel):
    answer: str
    session_id: str



#class ResumeUploadResponse(BaseModel):
#    filename: str
#    session_id: str
#    extracted_text: str
#
#
#
#class DeleteResumeRequest(BaseModel):
#    file_id: int
#
#
#
#class InterviewSessionInit(BaseModel):
#    session_id: str
#    interview_type: InterviewType
#    resume_text: str
#    user_object: Dict[str, str]  
#
#
#class QuestionFeedbackRequest(BaseModel):
#    session_id: str
#    question_index: int
#    question: str
#    user_answer: str
#    verdict: str  
#    feedback: str
#    score: float = 0.0
#    followup_question: Optional[str] = ""
#
#
#class ResumeDocumentInfo(BaseModel):
#    id: int
#    filename: str
#    session_id: str
#    upload_timestamp: datetime