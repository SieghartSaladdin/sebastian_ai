# app/memory.py
import os
import sqlite3
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.messages import SystemMessage

# Ensure memory folder exists
os.makedirs("memory", exist_ok=True)

DB_PATH = "sqlite:///memory/sessions.db"
DB_FILE = "memory/sessions.db"

def get_chat_history(session_id: str):
    """Retrieve (or create) an SQL memory object based on session_id."""
    history = SQLChatMessageHistory(
        session_id=session_id,
        connection=DB_PATH  # <-- Change 'connection_string' to 'connection'
    )
        
    return history

def list_sessions():
    """Retrieve the list of session_ids directly from the SQLite database."""
    try:
        # We connect manually using Python's built-in sqlite3 just to read the list of sessions
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # The default table created by LangChain is named 'message_store'
        cursor.execute("SELECT DISTINCT session_id FROM message_store")
        sessions = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return sessions
    except sqlite3.OperationalError:
        # If an error occurs (message_store table doesn't exist yet because there's no chat), return an empty list
        return []