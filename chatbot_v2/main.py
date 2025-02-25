
import os
import json
from google.cloud import secretmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, Text, TIMESTAMP, ForeignKey, JSON, Boolean
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime
from dotenv import load_dotenv
import anthropic 

load_dotenv()
PROJECT_ID = os.getenv("PROJECT_ID")


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler to show detailed validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": exc.body
        },
    )

# Function to access secrets from Google Cloud Secret Manager
def get_secret(secret_name):
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{PROJECT_ID}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(name=name)
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Error fetching secret {secret_name} from Secret Manager: {e}")
        raise

# Try to get API key from Secret Manager first; fallback to os.environ
def get_api_key():
    # load_dotenv()
    # return os.getenv("CLAUDE_API_KEY")
    try:
        return get_secret("claude_auth")
    except Exception:
        if "CLAUDE_API_KEY" in os.environ:
            load_dotenv()
            return os.getenv("CLAUDE_API_KEY")
        else:
            raise ValueError("API key for 'claude_auth' not found.")

# Try to get the database URI from Secret Manager first; fallback to os.environ
def get_db_uri():
    # load_dotenv()
    # return os.getenv("DATABASE_URI")
    try:
        return get_secret("db_uri")
    except Exception:
        if "DATABASE_URI" in os.environ:
            load_dotenv()
            return os.getenv("DATABASE_URI")
        else:
            raise ValueError("Database URI for 'db_uri' not found.")

engine = create_engine(get_db_uri(), connect_args={"sslmode": "require"})
metadata = MetaData()

conversations = Table(
    'conversations', metadata,
    Column('conversation_id', Integer, primary_key=True, autoincrement=True),
    Column('start_time', TIMESTAMP, default=datetime.now),
    Column('initial_rating', Integer),
    Column('final_rating', Integer),
    Column('proficiency', String(20)),
    Column('chatbot_version', String(20)),
    Column('usecase', String(20)),
    Column('age_group', String(50)),
    Column('gender', String(20)),
    Column('highest_degree', String(50)),
    Column('consent_given', Boolean, default=False),
    Column('usecase_specific_info', JSON)
)

messages = Table(
    'messages', metadata,
    Column('message_id', Integer, primary_key=True, autoincrement=True),
    Column('conversation_id', Integer, ForeignKey('conversations.conversation_id')),
    Column('role', String(20), nullable=False),
    Column('content', Text, nullable=False),
    Column('timestamp', TIMESTAMP, default=datetime.now),
    Column('message_type', String(50))
)

feedback = Table(
    'feedback', metadata,
    Column('feedback_id', Integer, primary_key=True, autoincrement=True),
    Column('conversation_id', Integer, ForeignKey('conversations.conversation_id')),
    Column('feedback_text', Text, nullable=False),
    Column('rating', Integer, nullable=True),
    Column('timestamp', TIMESTAMP, default=datetime.now)
)

metadata.create_all(engine)
SessionLocal = scoped_session(sessionmaker(bind=engine))

def load_chatbot_config():
    with open("chatbot_config.json", "r", encoding="utf-8") as f:
        return json.load(f)

chatbot_config = load_chatbot_config()
claude_client = anthropic.Client(api_key=get_api_key())

# -------------------------------
# Pydantic Models
# -------------------------------
class InitConversationRequest(BaseModel):
    proficiency: str
    consent_given: bool
    language: str = "en"
    usecase_specific_info: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ChatHistoryItem(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    conversation_id: int
    message: str
    history: List[ChatHistoryItem] = Field(default_factory=list)
    language: str

class FeedbackRequest(BaseModel):
    conversation_id: int
    feedback_text: str
    rating: Optional[int] = None

# -------------------------------
# DB Insert Helpers
# -------------------------------
def init_conversation(db, proficiency, consent_given, language, usecase_specific_info):
    ins = conversations.insert().values(
        start_time=datetime.now(),
        chatbot_version=chatbot_config.get("version", "unknown"),
        usecase=chatbot_config.get("usecase", "unknown"),
        proficiency=proficiency,
        consent_given=consent_given,
        usecase_specific_info=usecase_specific_info
    )
    result = db.execute(ins)
    db.commit()
    return result.inserted_primary_key[0]

def insert_message(db, conversation_id, role, content, message_type="conversation"):
    ins = messages.insert().values(
        conversation_id=conversation_id,
        role=role,
        content=content,
        timestamp=datetime.now(),
        message_type=message_type
    )
    db.execute(ins)
    db.commit()

def insert_feedback_db(db, conversation_id, feedback_text, rating=None):
    ins = feedback.insert().values(
        conversation_id=conversation_id,
        feedback_text=feedback_text,
        rating=rating,
        timestamp=datetime.now()
    )
    db.execute(ins)
    db.commit()

# -------------------------------
# API Endpoints
# -------------------------------
@app.post("/api/init")
def api_init_conversation(req: InitConversationRequest):
    db = SessionLocal()
    try:
        conv_id = init_conversation(
            db,
            proficiency=req.proficiency,
            consent_given=req.consent_given,
            language=req.language,
            usecase_specific_info=req.usecase_specific_info
        )

        lang_prompt = "Verwende die Deutsche Sprache." if req.language == "de" else "Use the English Language."
        solar_ownership = req.usecase_specific_info.get("solar_panel_ownership", "no")
        solar_prompt = (
            f"Solar Ownership: {solar_ownership}. "
            f"Based on this, emphasize these questions (concise and not all at once):"
            f"{chatbot_config['solar_ownership'][solar_ownership]['questions']} "
            f"User Proficiency Level: {req.proficiency}"
        )
        system_prompt = (
            f"{lang_prompt} If German, you can use a typical Swiss Greeting "
            f"{chatbot_config['general']['general_role']} "
            f"{chatbot_config[req.proficiency]['conversation_role']}"
        )

        response = claude_client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=chatbot_config[req.proficiency]["conversation_max_tokens"],
            temperature=chatbot_config[req.proficiency]["conversation_temperature"],
            system=system_prompt,
            messages=[{"role": "user", "content": solar_prompt}],
        )
        initial_message = response.content[0].text.strip()

        insert_message(db, conv_id, "assistant", initial_message)
        return {"conversation_id": conv_id, "initial_message": initial_message}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/api/chat")
def api_chat(req: ChatRequest):
    db = SessionLocal()
    try:
        insert_message(db, req.conversation_id, "user", req.message)
        context = "\n".join([f"{item.role}: {item.content}" for item in req.history])
        context += f"\nuser: {req.message}"
        language_prompt = " Please answer in German." if req.language == "de" else " Please answer in English."
        system_text = chatbot_config["general"]["general_role"] + language_prompt

        response = claude_client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=500,
            temperature=0.7,
            system=system_text,
            messages=[
                {"role": "assistant", "content": context},
                {"role": "user", "content": req.message},
            ]
        )
        assistant_text = response.content[0].text.strip()

        insert_message(db, req.conversation_id, "assistant", assistant_text)
        return {"response": assistant_text}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/api/feedback")
def api_feedback(req: FeedbackRequest):
    db = SessionLocal()
    try:
        insert_feedback_db(db, req.conversation_id, req.feedback_text, req.rating)
        return {"message": "Feedback submitted successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

class UpdateUsecaseRequest(BaseModel):
    conversation_id: int
    additional_info: Dict[str, Any]

@app.post("/api/update_usecase")
def update_usecase(req: UpdateUsecaseRequest):
    db = SessionLocal()
    try:
        result = db.execute(
            conversations.select().where(
                conversations.c.conversation_id == req.conversation_id
            )
        ).fetchone()
        if result is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        current_info = result._mapping.get("usecase_specific_info") or {}
        if not isinstance(current_info, dict):
            current_info = {}
        updated_info = {**current_info, **req.additional_info}
        db.execute(
            conversations.update().where(
                conversations.c.conversation_id == req.conversation_id
            ).values(usecase_specific_info=updated_info)
        )
        db.commit()
        return {"message": "Usecase info updated", "updated_info": updated_info}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/config")
def get_config():
    return chatbot_config
