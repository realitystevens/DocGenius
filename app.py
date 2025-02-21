import os
import io
import fitz
import redis
import google.generativeai as genai
import google.api_core.exceptions
from flask import Flask, request, render_template, jsonify

from dotenv import load_dotenv
load_dotenv()



app = Flask(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro-latest")

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=6379,
    db=0,
    password=os.getenv("REDIS_PASSWORD"),
    ssl=True,
    socket_timeout=10
)



def extractPDFText(file_stream):
    try:
        pdf_document = fitz.open(stream=file_stream, filetype="pdf")
        text = ""

        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text()

        redis_client.set("pdfTextCache", text)
        pdf_text = redis_client.get("pdfTextCache")

        return pdf_text
    except redis.RedisError as e:
        return f"Extract PDF text Redis Error: {e}"
    except ValueError as e:
        return f"Extract PDF text Value Error: {e}"
    except Exception as e:
        return f"Extract PDF text Error: {e}"   


def getAnswer(prompt):
    try:
        response = model.generate_content(prompt)
        """Extract response text correctly from the response object."""
        if response.candidates:
            answer = response.candidates[0].content.parts[0].text.strip()
        else:
            answer = "No response from AI."

        return {
            "answer": answer,
            "status_code": 200,  # Gemini API does not return status codes
        }
    except google.api_core.exceptions.GoogleAPIError as api_err:
        return {
            "answer": f"API Error: {api_err}",
            "status_code": 500,
        }
    except Exception as e:
        return {
            "answer": f"Unexpected Error: {e}",
            "status_code": 500,
        }


    

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/v1", methods=["POST"])
def api():
    extractedPDFText = ""
    result = ""
    file = request.files.get("file")
    question = request.form.get("question")

    if file:
        file_content = file.read()
        file_stream = io.BytesIO(file_content)
        extractedPDFText_io = extractPDFText(file_stream)
        extractedPDFText = extractedPDFText_io.decode("utf-8")

    if question and extractedPDFText:
        prompt = f"""
            You are an expert at extracting precise information from documents. 
            Use the following document text to answer the question as accurately as possible.
            If the answer is not in the document, say "I cannot find the answer in the provided document."

            Document Text:
            {extractedPDFText}

            Question: {question}

            Answer:
        """
        result = getAnswer(prompt)

    if result.get("status_code") == 429:
        return jsonify({
            "answer": "Rate limit exceeded. Please try again later.",
            "status_code": 429,
        })

    return jsonify({
        "extractedPDFText": extractedPDFText,
        "answer": result.get("answer"),
        "status_code": result.get("status_code"),
    })






if __name__ == "__main__":
    if os.getenv("ENV") == "development":
        app.run(debug=True)
    app.run(debug=False)
