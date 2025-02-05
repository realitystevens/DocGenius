import os
import PyPDF2
import cloudinary
import cloudinary.uploader
import google.generativeai as genai
from flask import Flask, request, render_template

from dotenv import load_dotenv
load_dotenv()



app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro-latest")




def extractPDFText(pdfPath):
    try:
        text = ""
        with open(pdfPath, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                pageText = page.extract_text()
                if pageText:
                    text += "\n\n" + pageText
        return text
    except Exception as e:
        return f"Error extracting text: {e}"


def getAnswer(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error getting answer: {e}"

    

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/v1", methods=["POST"])
def api():
    extractedPDFText = ""
    answer = ""
    file = request.files.get("file")
    question = request.form.get("question")

    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        extractedPDFText = extractPDFText(file_path)

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
        answer = getAnswer(prompt)

    if answer == "429 Resource has been exhausted (e.g. check quota).":
        answer = "API rate limit exceeded. Please try again later."

    return {
        "extractedPDFText": extractedPDFText,
        "answer": answer
    }






if __name__ == "__main__":
    if os.getenv("ENV") == "development":
        app.run(debug=True)
    app.run(debug=False)
