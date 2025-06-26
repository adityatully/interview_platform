import sqlite3
from datetime import datetime
import json
from langchain_community.document_loaders import PyPDFLoader
DB_NAME = "interview_app.db" 



def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_interview_tables():
    conn = get_db_connection()

    # 1. Interview session metadata (user, type, question list, etc.)
    conn.execute('''
    CREATE TABLE IF NOT EXISTS interview_sessions (
        session_id TEXT PRIMARY KEY,
        interview_type TEXT,
        user_object TEXT,             -- JSON string of parsed resume
        question_list TEXT,           -- JSON array of questions
        current_question_index INTEGER DEFAULT 0,
        active_agent TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 2. Chat history during interview (separate from app logs)
    conn.execute('''
    CREATE TABLE IF NOT EXISTS interview_chat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        role TEXT,                   -- 'user' or 'ai'
        message TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 3. Question-answer tracking with feedback
    conn.execute('''
    CREATE TABLE IF NOT EXISTS question_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        question TEXT,             
        feedback TEXT
    )
    ''')

    conn.commit()
    conn.close()

def insert_interview_session(session_id, interview_type, user_object, question_list, current_question_index, active_agent):
    conn = get_db_connection()
    conn.execute('''
        INSERT OR REPLACE INTO interview_sessions (
            session_id, interview_type, user_object, question_list, current_question_index, active_agent
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        session_id,
        interview_type,
        json.dumps(user_object),
        json.dumps(question_list),
        current_question_index,
        active_agent
    ))
    conn.commit()
    conn.close()

def get_interview_session(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM interview_sessions WHERE session_id = ?', (session_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "session_id": row["session_id"],
            "interview_type": row["interview_type"],
            "user_object": json.loads(row["user_object"]),
            "question_list": json.loads(row["question_list"]),
            "current_question_index": row["current_question_index"],
            "active_agent": row["active_agent"]
        }
    return None

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO interview_chat (session_id, role, message) VALUES (?, ?, ?)',
        (session_id, role, message)
    )
    conn.commit()
    conn.close()





def create_resume_text_table():
    conn = get_db_connection()
    conn.execute('''
    CREATE TABLE IF NOT EXISTS resume_texts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        filename TEXT,
        full_text TEXT,
        upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

def load_full_resume_text(file_path: str) -> str:
    """
    Loads the entire PDF content as a single string.
    Useful for summarization and DB storage.
    """
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    full_text = "\n\n".join([page.page_content for page in pages])
    return full_text

def insert_full_resume_text(file_path: str, session_id: str, filename: str) -> int:
    """
    Loads full text from PDF and inserts it into the resume_texts table.
    Returns the auto-generated file_id.
    """
    try:
        full_text = load_full_resume_text(file_path)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            '''
            INSERT INTO resume_texts (session_id, filename, full_text)
            VALUES (?, ?, ?)
            ''',
            (session_id, filename, full_text)
        )

        file_id = cursor.lastrowid  # get the auto-incremented ID
        conn.commit()
        conn.close()
        return file_id

    except Exception as e:
        print(f"Error inserting resume text: {e}")
        return -1  # Or raise Exception for better error handling

def get_full_resume_text(file_id: int) -> str:
   conn = get_db_connection()
   cursor = conn.cursor()
   cursor.execute('SELECT full_text FROM resume_texts WHERE file_id = ?', (file_id,))
   row = cursor.fetchone()
   conn.close()
   return row['full_text'] if row else None

def get_resume_text_by_session(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''
        SELECT full_text 
        FROM resume_texts 
        WHERE session_id = ? 
        ORDER BY upload_timestamp DESC 
        LIMIT 1
        ''',
        (session_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    return row["full_text"] if row else None

def delete_full_resume_text(file_id: int):
    conn = get_db_connection()
    conn.execute('DELETE FROM resume_texts WHERE file_id = ?', (file_id,))
    conn.commit()
    conn.close()




def insert_interview_chat(session_id, user_query, gpt_response):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        'INSERT INTO interview_chat (session_id, role, message) VALUES (?, ?, ?)',
        (session_id, 'user', user_query)
    )
    cursor.execute(
        'INSERT INTO interview_chat (session_id, role, message) VALUES (?, ?, ?)',
        (session_id, 'ai', gpt_response)
    )

    conn.commit()
    conn.close()
def get_interview_chat_history(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        'SELECT role, message FROM interview_chat WHERE session_id = ? ORDER BY timestamp',
        (session_id,)
    )
    messages = [{"role": row["role"], "content": row["message"]} for row in cursor.fetchall()]

    conn.close()
    return messages




def get_feedback_for_session(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM question_feedback WHERE session_id = ? ORDER BY question_index',
        (session_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    feedback_list = []
    for row in rows:
        feedback_list.append({
            "question_index": row["question_index"],
            "question": row["question"],
            "user_answer": row["user_answer"],
            "verdict": row["verdict"],
            "feedback": row["feedback"],
            "score": row["score"],
            "followup_question": row["followup_question"]
        })
    return feedback_list

def insert_question_feedback(session_id, question, feedback):
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO question_feedback (
            session_id, question, feedback
        ) VALUES (?, ?, ?)
    ''', (
        session_id, question,
         feedback
    ))
    conn.commit()
    conn.close()

def get_latest_feedback_entry(session_id: str):
    """
    Fetch the most recent question_feedback entry for the given session.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''
        SELECT question, verdict 
        FROM question_feedback 
        WHERE session_id = ? 
        ORDER BY question_index DESC 
        LIMIT 1
        ''',
        (session_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "question": row["question"],
            "verdict": row["verdict"]
        }
    return None


# Initialize the database tables
#create_application_logs()
#create_document_storage()
create_interview_tables()
create_resume_text_table()

print("Database tables created.")