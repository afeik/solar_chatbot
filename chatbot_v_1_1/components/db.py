# db.py

from datetime import datetime
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, Text, TIMESTAMP, ForeignKey, JSON, Boolean
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from .utils import get_db_uri
import streamlit as st


# Load database URI from Streamlit secrets
db_uri = get_db_uri()

# Ensure that db_uri includes 'sslmode=require'
if 'sslmode' not in db_uri:
    if '?' in db_uri:
        db_uri += '&sslmode=require'
    else:
        db_uri += '?sslmode=require'

# Initialize Metadata and Database Tables
metadata = MetaData()

# Define the conversations table
conversations = Table(
    'conversations', metadata,
    Column('conversation_id', Integer, primary_key=True, autoincrement=True),
    Column('start_time', TIMESTAMP, default=datetime.now),
    Column('initial_rating', Integer),  # Initial rating provided by the user
    Column('final_rating', Integer),    # Final rating provided by the user
    Column('proficiency', String(20)), # User's proficiency level
    Column('chatbot_version', String(20)), # Chatbot version used
    Column('usecase', String(20)), # Use case or scenario
    Column('age_group', String(50)), # User's age group
    Column('gender', String(20)), # User's gender
    Column('highest_degree', String(50)), # User's highest degree
    Column('consent_given', Boolean, nullable=False, default=False), # Whether consent is given
    Column('usecase_specific_info', JSON)  # New column for JSON data
)

# Define the messages table
messages = Table(
    'messages', metadata,
    Column('message_id', Integer, primary_key=True, autoincrement=True),
    Column('conversation_id', Integer, ForeignKey('conversations.conversation_id')),
    Column('role', String(20), nullable=False),
    Column('content', Text, nullable=False),
    Column('timestamp', TIMESTAMP, default=datetime.now),
    Column('message_type', String(50))
)

# Define the feedback table
feedback = Table(
    'feedback', metadata,
    Column('feedback_id', Integer, primary_key=True, autoincrement=True),
    Column('conversation_id', Integer, ForeignKey('conversations.conversation_id'), nullable=True),
    Column('feedback_text', Text, nullable=False),  # User feedback content
    Column('rating', Integer, nullable=True),  # Optional rating (1-5)
    Column('timestamp', TIMESTAMP, default=datetime.now, nullable=False)  # Feedback submission time
)

# Initialize Database Engine and Session Factory
engine = create_engine(
    db_uri,
    connect_args={"sslmode": "require"},
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=3600*24,
    pool_recycle=3600*24,  # Recycle connections every 30 minutes
    pool_pre_ping=True
)
# Create all tables in the database
metadata.create_all(engine)
Session = scoped_session(sessionmaker(bind=engine))


