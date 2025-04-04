"""
Utility functions for application.
"""

import os
import sqlite3
import google.generativeai as genai
import google.api_core.exceptions
from flask import jsonify



def logFiles():
    """
    Retrieve all files and their extracted text from the SQLite database.
    """
    db_path = os.path.join(os.getcwd(), "extracted_files.db")

    if not os.path.exists(db_path):
        return jsonify({
            "error": "Database file not found.",
            "status_code": 404,
        })
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT file_name, extracted_text FROM extracted_files
        """)
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            return jsonify({
                "error": "The database table 'extracted_files' does not exist. Please ensure the table is created.",
                "status_code": 500,
            })
        else:
            raise
    rows = cursor.fetchall()

    # Close the database connection
    conn.close()

    # Extract file names and their corresponding extracted text from the rows
    files = [{"file_name": row[0], "extracted_text": row[1]} for row in rows]

    return files


def getAnswer(extracted_text, question):
    """
    Generate an answer to the user's question 
    based on the extracted text from the document.
    """

    # Initialize the Google Generative AI API client
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-pro-latest")

    try:
        # Set the model parameters
        messages = [
            {
                "parts": [
                    {"text": "You are an AI assistant helping with document analysis."},
                    {"text": f"Document Content:\n{extracted_text}\n\nQuestion: {question}"}
                ]
            }
        ]

        response = model.generate_content(messages)

        # Extract the response text from the response object
        answer = (
            response.candidates[0].content.parts[0].text.strip()
            if response.candidates and response.candidates[0].content.parts
            else "No response from AI."
        )

        return {
            "answer": answer,
            "status_code": 200,
        }
    except google.api_core.exceptions.GoogleAPIError as api_error:
        return {
            "answer": f"API Error: {api_error.message}",
            "status_code": int(api_error.code) if hasattr(api_error, "code") else 500,
        }
    except Exception as e:
        return {
            "answer": f"Unexpected Error: {str(e)}",
            "status_code": 500,
        }


def saveConversations(user_question, ai_answer):
    """
    Save the conversation (user question and AI answer) to the SQLite database.
    """
    db_path = os.path.join(os.getcwd(), "conversations.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_question TEXT NOT NULL,
            ai_answer TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insert conversation into database
    cursor.execute("""
        INSERT INTO conversations (user_question, ai_answer)
        VALUES (?, ?)
    """, (user_question, ai_answer))

    # Commit transaction and close connection
    conn.commit()
    conn.close()

    return user_question, ai_answer


def logConversations():
    db_path = os.path.join(os.getcwd(), "conversations.db")
    if not os.path.exists(db_path):
        return jsonify({
            "error": "Database file not found.",
            "status_code": 404,
        })

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT user_question, ai_answer, timestamp FROM conversations
            ORDER BY timestamp ASC
        """)
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            return jsonify({
                "error": "The database table 'conversations' does not exist. Please ensure the table is created.",
                "status_code": 500,
            })
        else:
            raise

    rows = cursor.fetchall()
    conn.close()

    # Extract conversations from the rows
    conversations = [
        {"user_question": row[0], "ai_answer": row[1], "timestamp": row[2]}
        for row in rows
    ]

    return conversations
