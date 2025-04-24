"""
Utility functions for application.
"""

import os
import google.generativeai as genai
import google.api_core.exceptions
from dotenv import load_dotenv



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
