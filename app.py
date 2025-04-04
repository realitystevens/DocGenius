import os
import io
import sqlite3
from flask import Flask, request, render_template, jsonify
from utils.app_utils import logFiles, getAnswer, saveConversations, logConversations
from utils.extractText import extractPDFText, extractTXTText, extractDOCXText, extractPPTXText

from dotenv import load_dotenv
load_dotenv()





app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/v1/save_file", methods=["POST"])
def save_file():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided."}), 400

    file_name = file.filename
    _, file_extension = os.path.splitext(file_name)
    file_content = file.read()
    file_stream = io.BytesIO(file_content)

    if file_extension.lower() == ".pdf":
        extractedFileText = extractPDFText(file_stream)
    elif file_extension.lower() == ".txt":
        extractedFileText = extractTXTText(file_stream)
    elif file_extension.lower() == ".docx":
        extractedFileText = extractDOCXText(file_stream)
    elif file_extension.lower() == ".pptx":
        extractedFileText = extractPPTXText(file_stream)
    else:
        return jsonify({
            "error": "Unsupported file type. Please upload a PDF, TXT, DOCX, or PPTX file.",
            "status_code": 400,
        })

    # Connect to SQLite database (or create it if it doesn't exist)
    db_path = os.path.join(os.getcwd(), "extracted_files.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create a table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS extracted_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            extracted_text TEXT NOT NULL
        )
    """)

    # Insert the extracted text into the database
    cursor.execute("""
        INSERT INTO extracted_files (file_name, extracted_text)
        VALUES (?, ?)
    """, (file_name, extractedFileText))

    # Commit the transaction and close the connection
    conn.commit()
    conn.close()

    return jsonify({
        "message": "File saved and text extracted successfully.",
        "status_code": 200,
    })


@app.route("/api/v1/files", methods=["GET"])
def get_files():
    files = logFiles()

    return jsonify({
        "files": files,
        "status_code": 200,
    })


@app.route("/api/v1/conversations", methods=["GET"])
def get_conversations():
    """
    Retrieve all conversations from the SQLite database.
    """

    conversations = logConversations()

    return jsonify({
        "conversations": conversations,
        "status_code": 200,
    })


@app.route("/api/v1/ask_ai", methods=["POST"])
def askAI():
    """
    Ask the AI a question based on the 
    extracted text from the document.
    """
    extractedFileText = request.form.get("extractedFileText")
    user_question = request.form.get("question")
    ai_response = ""

    if not extractedFileText:
        return jsonify({
            "answer": "No text extracted from the file.",
            "status_code": 400,
        })

    if not user_question:
        return jsonify({
            "answer": "Please provide a question.",
            "status_code": 400,
        })

    if user_question and extractedFileText:
        ai_response = getAnswer(extractedFileText, user_question)

    if ai_response.get("status_code") == 429:
        return jsonify({
            "answer": "Rate limit exceeded. Please try again later.",
            "status_code": 429,
        })

    user_question, result = saveConversations(user_question, ai_response.get("answer"))

    return jsonify({
        "extractedFileText": extractedFileText,
        "user_question": user_question,
        "answer": result,
        "status_code": 200,
    })






if __name__ == "__main__":
    if os.getenv("ENV") == "development":
        app.run(debug=True)
    else:
        app.run(debug=False)
