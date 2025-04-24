import os
import io
import json
import uuid
import redis
from flask import Flask, request, render_template, jsonify, session
from flask_session import Session
from dotenv import load_dotenv
from utils.app_utils import getAnswer
from utils.extractText import (
    extractPDFText,
    extractTXTText,
    extractDOCXText,
    extractPPTXText,
)

load_dotenv()


app = Flask(__name__)

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=6379,
    password=os.getenv("REDIS_PASSWORD"),
    ssl=True
)

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")  
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_REDIS'] = redis_client

Session(app)


"""Set user_id if not already set, on every request"""
@app.before_request
def ensure_user_id():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())


@app.route("/")
def index():
    """
    Render the index page. 
    Note: Dynamic content and functionalities in index page 
    is handled by JavaScript on the frontend.
    """
    return render_template("index.html")


@app.route("/api/v1/process_file", methods=["POST"])
def process_file():
    """
    Recieve file from frontend, 
    extract its text and save the text on Redis.
    """
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided."}), 400

    file_name = file.filename
    _, file_extension = os.path.splitext(file_name)
    file_content = file.read()
    file_stream = io.BytesIO(file_content)

    # Extract text based on file type
    extractors = {
        ".pdf": extractPDFText,
        ".txt": extractTXTText,
        ".docx": extractDOCXText,
        ".pptx": extractPPTXText,
    }
    extractor = extractors.get(file_extension.lower())
    if not extractor:
        return jsonify({
            "error": "Unsupported file type. Please upload a PDF, TXT, DOCX, or PPTX file.",
            "status_code": 400,
        })

    extractedFileText = extractor(file_stream)

    # Set user_id from session
    user_id = session['user_id']

    # Store the file data in Redis
    file_data = {
        "file_name": file_name,
        "extracted_text": extractedFileText
    }
    redis_key = f"user:{user_id}:files"
    redis_client.rpush(redis_key, json.dumps(file_data))

    return jsonify({
        "message": "File saved and text extracted successfully.",
        "status_code": 200,
    })


@app.route("/api/v1/files", methods=["GET"])
def get_files():
    """Retrieve all files and their extracted text from Redis."""
    try:
        
        # Set user_id from session
        user_id = session.get('user_id')

        redis_key = f"user:{user_id}:files"
        files = redis_client.lrange(redis_key, 0, -1)
        files = [json.loads(file) for file in files]

        if not files:
            return jsonify({
                "error": "No files found.",
                "status_code": 404,
            })

        return jsonify({
            "files": files,
            "status_code": 200,
        })
    except redis.RedisError as e:
        return jsonify({
            "error": f"Redis Error: {str(e)}",
            "status_code": 500,
        })


@app.route("/api/v1/conversations", methods=["GET"])
def get_conversations():
    """Retrieve all conversations from Redis."""
    user_id = session.get('user_id')

    keys = redis_client.keys(f"conversation:{user_id}:*")
    if not keys:
        return jsonify({
            "error": "No conversations found.",
            "status_code": 404,
        })

    conversations = []
    for key in keys:
        conversation = redis_client.hgetall(key)
        conversations.append({
            "user_question": conversation.get(b"user_question", b"").decode(),
            "ai_answer": conversation.get(b"ai_answer", b"").decode(),
            "timestamp": conversation.get(b"timestamp", b"").decode(),
        })

    return jsonify({
        "conversations": conversations,
        "status_code": 200,
    })


@app.route("/api/v1/ask_ai", methods=["POST"])
def askAI():
    """Ask the AI a question based on the extracted text."""
    user_id = session['user_id']
    extractedFileText = request.form.get("extractedFileText")
    user_question = request.form.get("question")

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

    ai_response = getAnswer(extractedFileText, user_question)
    if ai_response.get("status_code") == 429:
        return jsonify({
            "answer": "Rate limit exceeded. Please try again later.",
            "status_code": 429,
        })

    result = ai_response.get("answer")
    if not result:
        return jsonify({
            "answer": "No answer generated.",
            "status_code": 500,
        })

    # Save the conversation in Redis
    conversation_id = str(uuid.uuid4())
    redis_client.hset(f"conversation:{user_id}:{conversation_id}", mapping={
        "user_question": user_question,
        "ai_answer": result,
        "timestamp": str(uuid.uuid1())
    })

    return jsonify({
        "extractedFileText": extractedFileText,
        "user_question": user_question,
        "answer": result,
        "status_code": 200,
    })






if __name__ == "__main__":
    app.run(debug=os.getenv("ENV") == "development")
