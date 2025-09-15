"""
API blueprint for handling all API endpoints.
"""

import os
import uuid
from datetime import datetime
from functools import wraps
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename

from app.services.ai_service import AIService
from app.services.file_service import FileService
from app.services.conversation_service import ConversationService
from app.utils.validators import validate_file, validate_question
from app.utils.exceptions import DocGeniusException

api_bp = Blueprint('api', __name__)

# Initialize services
ai_service = AIService()
file_service = FileService()
conversation_service = ConversationService()


def require_redis(f):
    """Decorator to ensure Redis is available for API endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not getattr(current_app, 'redis_available', False):
            error_msg = getattr(current_app, 'redis_error',
                                'Redis connection required')
            return jsonify({
                'error': 'Service temporarily unavailable',
                'details': error_msg,
                'status_code': 503
            }), 503
        return f(*args, **kwargs)
    return decorated_function


@api_bp.route('/files', methods=['POST'])
@require_redis
def upload_file():
    """
    Upload and process a document file.

    Accepts: PDF, TXT, DOCX, PPTX files
    Returns: File metadata and extracted text preview
    """
    try:
        # Validate request
        if 'file' not in request.files:
            return jsonify({
                'error': 'No file provided',
                'status_code': 400
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'error': 'No file selected',
                'status_code': 400
            }), 400

        # Validate file
        validation_result = validate_file(file)
        if not validation_result['valid']:
            return jsonify({
                'error': validation_result['error'],
                'status_code': 400
            }), 400

        # Process file
        result = file_service.process_file(file, session['user_id'])

        return jsonify({
            'message': 'File processed successfully',
            'file_id': result['file_id'],
            'file_name': result['file_name'],
            'file_size': result['file_size'],
            'text_preview': result['text_preview'],
            'word_count': result['word_count'],
            'status_code': 200
        }), 200

    except DocGeniusException as e:
        return jsonify({
            'error': str(e),
            'status_code': e.status_code
        }), e.status_code
    except Exception as e:
        current_app.logger.error(f"File upload error: {str(e)}")
        return jsonify({
            'error': 'Internal server error during file processing',
            'status_code': 500
        }), 500


@api_bp.route('/files', methods=['GET'])
@require_redis
def get_files():
    """
    Retrieve all files for the current user.

    Returns: List of user's uploaded files with metadata
    """
    try:
        files = file_service.get_user_files(session['user_id'])

        return jsonify({
            'files': files,
            'count': len(files),
            'status_code': 200
        }), 200

    except Exception as e:
        current_app.logger.error(f"Get files error: {str(e)}")
        return jsonify({
            'error': 'Failed to retrieve files',
            'status_code': 500
        }), 500


@api_bp.route('/files/<file_id>', methods=['DELETE'])
@require_redis
def delete_file(file_id):
    """
    Delete a specific file.

    Args:
        file_id: UUID of the file to delete
    """
    try:
        success = file_service.delete_file(file_id, session['user_id'])

        if success:
            return jsonify({
                'message': 'File deleted successfully',
                'status_code': 200
            }), 200
        else:
            return jsonify({
                'error': 'File not found or unauthorized',
                'status_code': 404
            }), 404

    except Exception as e:
        current_app.logger.error(f"Delete file error: {str(e)}")
        return jsonify({
            'error': 'Failed to delete file',
            'status_code': 500
        }), 500


@api_bp.route('/chat', methods=['POST'])
@require_redis
def ask_ai():
    """
    Ask the AI a question about a document.

    Request body:
        file_id: UUID of the document to analyze
        question: User's question about the document
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'error': 'No JSON data provided',
                'status_code': 400
            }), 400

        file_id = data.get('file_id')
        question = data.get('question')

        # Validate inputs
        if not file_id:
            return jsonify({
                'error': 'File ID is required',
                'status_code': 400
            }), 400

        question_validation = validate_question(question)
        if not question_validation['valid']:
            return jsonify({
                'error': question_validation['error'],
                'status_code': 400
            }), 400

        # Get file content
        file_data = file_service.get_file_content(file_id, session['user_id'])
        if not file_data:
            return jsonify({
                'error': 'File not found or unauthorized',
                'status_code': 404
            }), 404

        # Generate AI response
        ai_response = ai_service.generate_answer(
            document_content=file_data['extracted_text'],
            question=question,
            context={
                'file_name': file_data['file_name'],
                'user_id': session['user_id']
            }
        )

        # Save conversation
        conversation_id = conversation_service.save_conversation(
            user_id=session['user_id'],
            file_id=file_id,
            question=question,
            answer=ai_response['answer']
        )

        return jsonify({
            'conversation_id': conversation_id,
            'question': question,
            'answer': ai_response['answer'],
            'file_name': file_data['file_name'],
            'timestamp': datetime.utcnow().isoformat(),
            'status_code': 200
        }), 200

    except DocGeniusException as e:
        return jsonify({
            'error': str(e),
            'status_code': e.status_code
        }), e.status_code
    except Exception as e:
        current_app.logger.error(f"AI chat error: {str(e)}")
        return jsonify({
            'error': 'Failed to process AI request',
            'status_code': 500
        }), 500


@api_bp.route('/conversations', methods=['GET'])
def get_conversations():
    """
    Retrieve conversation history for the current user.

    Query parameters:
        limit: Maximum number of conversations to return (default: 50)
        file_id: Filter conversations by specific file (optional)
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        file_id = request.args.get('file_id')

        conversations = conversation_service.get_user_conversations(
            user_id=session['user_id'],
            limit=limit,
            file_id=file_id
        )

        return jsonify({
            'conversations': conversations,
            'count': len(conversations),
            'status_code': 200
        }), 200

    except Exception as e:
        current_app.logger.error(f"Get conversations error: {str(e)}")
        return jsonify({
            'error': 'Failed to retrieve conversations',
            'status_code': 500
        }), 500


@api_bp.route('/conversations/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """
    Delete a specific conversation.

    Args:
        conversation_id: UUID of the conversation to delete
    """
    try:
        success = conversation_service.delete_conversation(
            conversation_id, session['user_id']
        )

        if success:
            return jsonify({
                'message': 'Conversation deleted successfully',
                'status_code': 200
            }), 200
        else:
            return jsonify({
                'error': 'Conversation not found or unauthorized',
                'status_code': 404
            }), 404

    except Exception as e:
        current_app.logger.error(f"Delete conversation error: {str(e)}")
        return jsonify({
            'error': 'Failed to delete conversation',
            'status_code': 500
        }), 500


@api_bp.route('/analytics', methods=['GET'])
def get_analytics():
    """
    Get usage analytics for the current user.

    Returns: User statistics and usage patterns
    """
    try:
        analytics = {
            'files_uploaded': file_service.get_file_count(session['user_id']),
            'conversations_count': conversation_service.get_conversation_count(session['user_id']),
            'total_questions_asked': conversation_service.get_question_count(session['user_id']),
            'user_id': session['user_id']
        }

        return jsonify({
            'analytics': analytics,
            'status_code': 200
        }), 200

    except Exception as e:
        current_app.logger.error(f"Analytics error: {str(e)}")
        return jsonify({
            'error': 'Failed to retrieve analytics',
            'status_code': 500
        }), 500
