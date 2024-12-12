import os
import sys
import PyPDF2
from dotenv import load_dotenv
from google.generativeai import genai
from flask import Flask, request, jsonify



load_dotenv()

app = Flask(__name__)


class DocGenius:
    def __init__(self):
        """ Configure Gemini AI API """
        try:
            GEMINI_APIKEY = os.getenv("GEMINI_APIKEY")
            if not GEMINI_APIKEY:
                raise ValueError("Gemini API key not found. Please configure GEMINI_APIKEY in .env file")
            
            genai.configure(api_key = GEMINI_APIKEY)

            """ Initialize the model """
            self.model = genai.GenerativeModel("gemini-1.5-pro-latest")
            self.pdfText = ""
        except Exception as e:
            print(f"Initialization error: {e}")
            sys.exit(1)



    def extractText(self, pdfPath):
        """
        Extract text from PDF file.

        Args:
            pdfPath (str): Path to PDF file

        Returns:
            str: Extracted text from PDF file
        """
        try:
            text = ""
            with open(pdfPath, "rb") as file:
                reader = PyPDF2.PdfReader(file)

                for page in reader.pages:
                    pageText = page.extract_text()

                    if pageText:
                        text += pageText + "\n\n"
            return text
        except Exception as e:
            return f"Error extracting text: {e}"



    def loadPDF(self, pdfPath):
        """
        Load and process a PDF file

        Args:
            pdfPath (str): Path to the PDF file
        """
        # Validate if PDF file exists
        if not os.path.exists(pdfPath):
            return f"Error: File {pdfPath} does not exist"

        # Set up extracted text
        self.pdfText = self.extractText(pdfPath)

        # Check if text extraction was successful
        if not self.pdfText:
            return "Failed to extract text from PDF file on loading the file"

        return "Successfully loaded PDF and extracted text. Total characters: {len(self.pdfText)}"
    


    def askQuestion(self, question):
        """
        Ask a question about the loaded PDF

        Args:
            question (str): Question to ask

        Returns:
            str: Answer from the AI
        """
        # Validate if PDF is loaded
        if not self.pdfText:
            return "Please load a PDF first using 'load [path to PDF]'"

        try:
            # Prepare the prompt
            prompt = f"""
            You are an expert at extracting precise information from documents. 
            Use the following document text to answer the question as accurately as possible.
            If the answer is not in the document, say "I cannot find the answer in the provided document."

            Document Text:
            {self.pdfText}

            Question: {question}

            Answer:
            """

            response = self.model.generate_content(prompt)

            return response.text.strip()

        except Exception as e:
            return f"Error processing question: {e}"




""" Initialize the DocGenius class """
project = DocGenius()


@app.route("/")
def index():
    return "DocGenius API"


@app.route("/upload", methods=["POST"])
def upload():
    data = request.json
    pdfPath = data.get("pdfPath")
    if not pdfPath:
        return jsonify({"error": "PDF path is required"}), 400
    result = project.loadPDF(pdfPath)

    return jsonify({"message": result})


@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    question = data.get("question")
    if not question:
        return jsonify({"error": "Question is required"}), 400
    answer = project.askQuestion(question)
    
    return jsonify({"answer": answer})





if __name__ == "__main__":
    app.run(debug=True)