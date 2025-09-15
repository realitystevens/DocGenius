"""
Enhanced AI service using Google's Gemini API with improved prompt engineering.
"""

import os
import time
import logging
from typing import Dict, Any, Optional
from functools import wraps

import google.generativeai as genai
import google.api_core.exceptions
from flask import current_app

from app.utils.exceptions import AIServiceException

logger = logging.getLogger(__name__)


def retry_on_rate_limit(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry API calls on rate limit errors."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except google.api_core.exceptions.ResourceExhausted as e:
                    if attempt == max_retries - 1:
                        raise AIServiceException(
                            "Rate limit exceeded. Please try again later.",
                            status_code=429
                        )
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(delay)
            return func(*args, **kwargs)
        return wrapper
    return decorator


class AIService:
    """Enhanced AI service for document analysis and question answering."""

    def __init__(self):
        """Initialize the AI service with Gemini configuration."""
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")

        genai.configure(api_key=self.api_key)
        self.model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-pro-latest')
        self.model = genai.GenerativeModel(self.model_name)

        # Configure generation parameters
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.3,  # Lower temperature for more consistent responses
            top_p=0.8,
            top_k=40,
            max_output_tokens=2048,
        )

        # Safety settings
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]

    def _create_system_prompt(self) -> str:
        """Create a comprehensive system prompt for document analysis."""
        return """You are DocGenius, an advanced AI assistant specialized in document analysis and question answering.

Your capabilities:
- Analyze and understand various types of documents (PDFs, text files, presentations, etc.)
- Provide accurate, detailed answers based on document content
- Summarize complex information clearly
- Extract specific data points and insights
- Maintain context across conversations

Guidelines:
- Always base your answers on the provided document content
- If information is not in the document, clearly state this
- Provide specific references to relevant sections when possible
- Use clear, professional language
- Structure your responses logically
- If asked about confidential or sensitive information, handle appropriately

Response format:
- Be concise but comprehensive
- Use bullet points or numbered lists for clarity when appropriate
- Highlight key findings or important information
- Provide actionable insights when relevant"""

    def _create_user_prompt(self, document_content: str, question: str, context: Dict[str, Any]) -> str:
        """Create a user prompt with document content and question."""
        file_name = context.get('file_name', 'Unknown Document')

        prompt = f"""Document Analysis Request

Document: {file_name}
Content:
{document_content[:8000]}  # Limit content to avoid token limits

Question: {question}

Please analyze the document and provide a comprehensive answer to the question based on the content above."""

        return prompt

    @retry_on_rate_limit(max_retries=3, delay=1.0)
    def generate_answer(self, document_content: str, question: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate an AI answer based on document content and user question.

        Args:
            document_content: Extracted text from the document
            question: User's question about the document
            context: Additional context (file_name, user_id, etc.)

        Returns:
            Dictionary containing the answer and metadata
        """
        if not document_content or not document_content.strip():
            raise AIServiceException("Document content is empty or invalid")

        if not question or not question.strip():
            raise AIServiceException("Question cannot be empty")

        context = context or {}

        try:
            # Prepare the conversation
            system_prompt = self._create_system_prompt()
            user_prompt = self._create_user_prompt(
                document_content, question, context)

            # Generate response
            chat = self.model.start_chat(history=[])

            # Send system prompt first
            chat.send_message(
                system_prompt,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )

            # Send user question
            response = chat.send_message(
                user_prompt,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )

            # Extract answer from response
            if response.candidates and response.candidates[0].content.parts:
                answer = response.candidates[0].content.parts[0].text.strip()
            else:
                raise AIServiceException("No valid response generated by AI")

            # Log successful generation
            logger.info(
                f"AI response generated for user {context.get('user_id', 'unknown')}")

            return {
                'answer': answer,
                'model_used': self.model_name,
                'token_count': self._estimate_tokens(user_prompt + answer),
                'status_code': 200
            }

        except google.api_core.exceptions.InvalidArgument as e:
            logger.error(f"Invalid argument error: {str(e)}")
            raise AIServiceException("Invalid input provided to AI service")

        except google.api_core.exceptions.ResourceExhausted as e:
            logger.error(f"Rate limit exceeded: {str(e)}")
            raise AIServiceException(
                "Rate limit exceeded. Please try again later.", status_code=429)

        except google.api_core.exceptions.PermissionDenied as e:
            logger.error(f"Permission denied: {str(e)}")
            raise AIServiceException(
                "AI service access denied. Please check API configuration.")

        except google.api_core.exceptions.GoogleAPIError as e:
            logger.error(f"Google API error: {str(e)}")
            raise AIServiceException(f"AI service error: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error in AI service: {str(e)}")
            raise AIServiceException(
                "An unexpected error occurred while processing your request")

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for a given text (rough approximation)."""
        # Rough estimation: 1 token ≈ 4 characters for English text
        return len(text) // 4

    def generate_summary(self, document_content: str, max_length: int = 200) -> Dict[str, Any]:
        """
        Generate a summary of the document content.

        Args:
            document_content: Text to summarize
            max_length: Maximum length of summary in words

        Returns:
            Dictionary containing the summary and metadata
        """
        summary_prompt = f"""Please provide a concise summary of the following document in approximately {max_length} words:

{document_content[:6000]}

Focus on the key points, main topics, and important information."""

        try:
            response = self.model.generate_content(
                summary_prompt,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )

            if response.candidates and response.candidates[0].content.parts:
                summary = response.candidates[0].content.parts[0].text.strip()
                return {
                    'summary': summary,
                    'word_count': len(summary.split()),
                    'status_code': 200
                }
            else:
                raise AIServiceException("Failed to generate summary")

        except Exception as e:
            logger.error(f"Summary generation error: {str(e)}")
            raise AIServiceException("Failed to generate document summary")

    def extract_key_points(self, document_content: str, num_points: int = 5) -> Dict[str, Any]:
        """
        Extract key points from the document.

        Args:
            document_content: Text to analyze
            num_points: Number of key points to extract

        Returns:
            Dictionary containing key points and metadata
        """
        key_points_prompt = f"""Analyze the following document and extract the {num_points} most important key points:

{document_content[:6000]}

Format the response as a numbered list of key points."""

        try:
            response = self.model.generate_content(
                key_points_prompt,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )

            if response.candidates and response.candidates[0].content.parts:
                key_points = response.candidates[0].content.parts[0].text.strip(
                )
                return {
                    'key_points': key_points,
                    'status_code': 200
                }
            else:
                raise AIServiceException("Failed to extract key points")

        except Exception as e:
            logger.error(f"Key points extraction error: {str(e)}")
            raise AIServiceException(
                "Failed to extract key points from document")
