# db_functions.py

from datetime import datetime
import streamlit as st
from sqlalchemy.sql import insert, update
from sqlalchemy.exc import SQLAlchemyError

# Import database session and table definitions from db.py
from .db import Session, conversations, messages, feedback
from .utils import get_chatbot_config

# Load chatbot configuration
chatbot_config = get_chatbot_config()

def init_db_communication():
    """Initialize a new conversation if none exists in session_state."""
    #if "conversation_id" in st.session_state and st.session_state.conversation_id is not None:
        #return  # Already initialized

    session = Session()
    try:
        result = session.execute(
            insert(conversations).values(
                start_time=datetime.now(),
                chatbot_version=chatbot_config.get("version", "unknown"),
                usecase=chatbot_config.get("usecase", "unknown")
            )
        )
        session.commit()
        st.session_state.conversation_id = result.inserted_primary_key[0]
    except SQLAlchemyError as e:
        session.rollback()
        st.error(f"Database error during conversation initialization: {e}")
    finally:
        session.close()


def insert_db_message(message, role, message_type):
    """Insert a message into the messages table."""
    if "conversation_id" not in st.session_state or st.session_state.conversation_id is None:
        init_db_communication()
    session = Session()
    try:
        session.execute(
            insert(messages).values(
                conversation_id=st.session_state.conversation_id,
                role=role,
                content=message,
                message_type=message_type,
                timestamp=datetime.now()
            )
        )
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        #st.error(f"Database error during message insertion: {e}")
    finally:
        session.close()

def insert_initial_rating(rating):
    """Insert the initial rating for a conversation."""
    session = Session()
    try:
        session.execute(
            update(conversations).where(
                conversations.c.conversation_id == st.session_state.conversation_id
            ).values(initial_rating=rating)
        )
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        #st.error(f"Database error during initial rating insertion: {e}")
    finally:
        session.close()

def insert_final_rating(rating):
    """Insert the final rating for a conversation."""
    session = Session()
    try:
        session.execute(
            update(conversations).where(
                conversations.c.conversation_id == st.session_state.conversation_id
            ).values(final_rating=rating)
        )
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        #st.error(f"Database error during final rating insertion: {e}")
    finally:
        session.close()

def update_proficiency():
    """Update the proficiency level for a conversation."""
    session = Session()
    try:
        session.execute(
            update(conversations).where(
                conversations.c.conversation_id == st.session_state.conversation_id
            ).values(proficiency=st.session_state.proficiency)
        )
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        #st.error(f"Database error during proficiency update: {e}")
    finally:
        session.close()

def insert_full_conversation_details(age_group, gender, highest_degree, consent_given):
    """
    Insert additional conversation details into the database.

    Args:
        age_group (str): User's age group.
        gender (str): User's gender.
        highest_degree (str): User's highest degree.
        consent_given (bool): Whether the user gave consent.

    Returns:
        None
    """
    if "conversation_id" not in st.session_state:
        init_db_communication()  # Ensure a conversation is initialized before inserting details

    session = Session()
    try:
        # Update the existing conversation with additional details
        session.execute(
            update(conversations).where(
                conversations.c.conversation_id == st.session_state.conversation_id
            ).values(
                age_group=age_group,
                gender=gender,
                highest_degree=highest_degree,
                consent_given=consent_given
            )
        )
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        #st.error(f"Database error during full conversation details insertion: {e}")
    finally:
        session.close()


def insert_feedback(feedback_text, rating=None):
    """
    Insert feedback into the feedback table.
    
    Args:
        feedback_text (str): The user's feedback.
        rating (int): The user's star rating (optional).
        
    Returns:
        None
    """
    if "conversation_id" not in st.session_state or st.session_state.conversation_id is None:
        st.error("No active conversation. Please ensure a conversation is initialized.")
        return

    session = Session()
    try:
        if rating is not None:
            session.execute(
                insert(feedback).values(
                    conversation_id=st.session_state.conversation_id,  # Link feedback to the active conversation
                    feedback_text=feedback_text,
                    rating=rating,
                    timestamp=datetime.now()
                )
            )
        else: 
                session.execute(
                insert(feedback).values(
                    conversation_id=st.session_state.conversation_id,  # Link feedback to the active conversation
                    feedback_text=feedback_text,
                    timestamp=datetime.now()
                )
            )
            
        session.commit()
        st.success(_("Feedback successfully submitted."))
    except SQLAlchemyError as e:
        session.rollback()
        #st.error(f"Database error during feedback insertion: {e}")
    finally:
        session.close()



def insert_usecase_specific_info(usecase_specific_info):
    """
    Insert usecase specific information into the database for the current conversation.

    Args:
        usecase_specific_info (dict): The use case specific information to be inserted (as a JSON object).
    """
    if "conversation_id" not in st.session_state:
        st.error("No active conversation. Please ensure a conversation is initialized.")
        return

    session = Session()
    try:
        # Update the existing conversation with the usecase specific information
        session.execute(
            update(conversations).where(
                conversations.c.conversation_id == st.session_state.conversation_id
            ).values(
                usecase_specific_info=usecase_specific_info  # Insert the JSON data
            )
        )
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        st.error(f"Database error during usecase specific info insertion: {e}")
    finally:
        session.close()