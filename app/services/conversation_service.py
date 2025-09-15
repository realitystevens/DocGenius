"""
Conversation service for managing chat history and interactions.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from flask import current_app

from app.utils.exceptions import ConversationException


class ConversationService:
    """Service for managing conversation history and analytics."""

    def __init__(self):
        """Initialize the conversation service."""
        self.redis_client = None

    def _get_redis_client(self):
        """Get Redis client from current app."""
        if not self.redis_client:
            self.redis_client = current_app.redis_client
        return self.redis_client

    def _redis_available(self):
        """Check if Redis is available."""
        return hasattr(current_app, 'redis_available') and current_app.redis_available

    def save_conversation(self, user_id: str, file_id: str, question: str, answer: str) -> str:
        """
        Save a conversation to Redis.

        Args:
            user_id: User's session ID
            file_id: Associated file ID
            question: User's question
            answer: AI's answer

        Returns:
            Conversation ID
        """
        conversation_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        try:
            conversation_data = {
                'conversation_id': conversation_id,
                'user_id': user_id,
                'file_id': file_id,
                'question': question,
                'answer': answer,
                'timestamp': timestamp
            }

            redis_client = self._get_redis_client()

            # Store conversation details
            redis_client.hset(
                f"conversation:{conversation_id}", mapping=conversation_data)

            # Add to user's conversation list (newest first)
            redis_client.lpush(
                f"user_conversations:{user_id}", conversation_id)

            # Add to file's conversation list
            redis_client.lpush(
                f"file_conversations:{file_id}", conversation_id)

            # Set expiration (90 days)
            redis_client.expire(
                f"conversation:{conversation_id}", 90 * 24 * 60 * 60)

            return conversation_id

        except Exception as e:
            current_app.logger.error(f"Error saving conversation: {str(e)}")
            raise ConversationException("Failed to save conversation")

    def get_user_conversations(self, user_id: str, limit: int = 50, file_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get conversations for a user.

        Args:
            user_id: User's session ID
            limit: Maximum number of conversations to return
            file_id: Optional file ID to filter conversations

        Returns:
            List of conversation dictionaries
        """
        try:
            conversations = []

            if self._redis_available():
                redis_client = self._get_redis_client()

                if file_id:
                    # Get conversations for specific file
                    conversation_ids = redis_client.lrange(
                        f"file_conversations:{file_id}", 0, limit - 1)
                else:
                    # Get all user conversations
                    conversation_ids = redis_client.lrange(
                        f"user_conversations:{user_id}", 0, limit - 1)

                for conversation_id in conversation_ids:
                    conversation_data = redis_client.hgetall(
                        f"conversation:{conversation_id}")

                    if conversation_data and conversation_data.get('user_id') == user_id:
                        # Get file name for context
                        file_data = redis_client.hgetall(
                            f"file:{conversation_data.get('file_id', '')}")
                        file_name = file_data.get(
                            'file_name', 'Unknown File') if file_data else 'Unknown File'

                        conversations.append({
                            'conversation_id': conversation_id,
                            'file_id': conversation_data.get('file_id', ''),
                            'file_name': file_name,
                            'question': conversation_data.get('question', ''),
                            'answer': conversation_data.get('answer', ''),
                            'timestamp': conversation_data.get('timestamp', '')
                        })
            else:
                # Fallback to session storage
                from flask import session
                session_conversations = session.get('conversations', {})
                user_conversation_ids = session.get(
                    'user_conversations', {}).get(user_id, [])

                for conversation_id in user_conversation_ids[:limit]:
                    if conversation_id in session_conversations:
                        conversation_data = session_conversations[conversation_id]

                        # Filter by file_id if specified
                        if file_id and conversation_data.get('file_id') != file_id:
                            continue

                        # Get file name from session
                        session_files = session.get('files', {})
                        file_data = session_files.get(
                            conversation_data.get('file_id', ''), {})
                        file_name = file_data.get('file_name', 'Unknown File')

                        conversations.append({
                            'conversation_id': conversation_id,
                            'file_id': conversation_data.get('file_id', ''),
                            'file_name': file_name,
                            'question': conversation_data.get('question', ''),
                            'answer': conversation_data.get('answer', ''),
                            'timestamp': conversation_data.get('timestamp', '')
                        })

            return conversations

        except Exception as e:
            current_app.logger.error(
                f"Error retrieving conversations: {str(e)}")
            return []

    def get_conversation(self, conversation_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific conversation.

        Args:
            conversation_id: Conversation ID
            user_id: User's session ID

        Returns:
            Conversation data or None if not found
        """
        redis_client = self._get_redis_client()

        try:
            conversation_data = redis_client.hgetall(
                f"conversation:{conversation_id}")

            if not conversation_data or conversation_data.get('user_id') != user_id:
                return None

            # Get file name for context
            file_data = redis_client.hgetall(
                f"file:{conversation_data.get('file_id', '')}")
            file_name = file_data.get(
                'file_name', 'Unknown File') if file_data else 'Unknown File'

            return {
                'conversation_id': conversation_id,
                'file_id': conversation_data.get('file_id', ''),
                'file_name': file_name,
                'question': conversation_data.get('question', ''),
                'answer': conversation_data.get('answer', ''),
                'timestamp': conversation_data.get('timestamp', '')
            }

        except Exception as e:
            current_app.logger.error(
                f"Error retrieving conversation: {str(e)}")
            return None

    def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: Conversation ID
            user_id: User's session ID

        Returns:
            True if deleted successfully, False otherwise
        """
        redis_client = self._get_redis_client()

        try:
            # Check if conversation exists and belongs to user
            conversation_data = redis_client.hgetall(
                f"conversation:{conversation_id}")

            if not conversation_data or conversation_data.get('user_id') != user_id:
                return False

            file_id = conversation_data.get('file_id', '')

            # Delete conversation data
            redis_client.delete(f"conversation:{conversation_id}")

            # Remove from user's conversation list
            redis_client.lrem(
                f"user_conversations:{user_id}", 0, conversation_id)

            # Remove from file's conversation list
            if file_id:
                redis_client.lrem(
                    f"file_conversations:{file_id}", 0, conversation_id)

            return True

        except Exception as e:
            current_app.logger.error(f"Error deleting conversation: {str(e)}")
            return False

    def get_conversation_count(self, user_id: str) -> int:
        """Get the total number of conversations for a user."""
        redis_client = self._get_redis_client()
        try:
            return redis_client.llen(f"user_conversations:{user_id}")
        except Exception:
            return 0

    def get_question_count(self, user_id: str) -> int:
        """Get the total number of questions asked by a user."""
        # For now, this is the same as conversation count
        # Could be extended to track other metrics
        return self.get_conversation_count(user_id)

    def get_file_conversation_count(self, file_id: str) -> int:
        """Get the number of conversations for a specific file."""
        redis_client = self._get_redis_client()
        try:
            return redis_client.llen(f"file_conversations:{file_id}")
        except Exception:
            return 0

    def search_conversations(self, user_id: str, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search conversations by question or answer content.

        Args:
            user_id: User's session ID
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching conversations
        """
        redis_client = self._get_redis_client()
        query_lower = query.lower()

        try:
            # Get all user conversations
            conversation_ids = redis_client.lrange(
                f"user_conversations:{user_id}", 0, -1)

            matching_conversations = []
            for conversation_id in conversation_ids:
                if len(matching_conversations) >= limit:
                    break

                conversation_data = redis_client.hgetall(
                    f"conversation:{conversation_id}")

                if conversation_data:
                    question = conversation_data.get('question', '').lower()
                    answer = conversation_data.get('answer', '').lower()

                    # Check if query matches question or answer
                    if query_lower in question or query_lower in answer:
                        # Get file name for context
                        file_data = redis_client.hgetall(
                            f"file:{conversation_data.get('file_id', '')}")
                        file_name = file_data.get(
                            'file_name', 'Unknown File') if file_data else 'Unknown File'

                        matching_conversations.append({
                            'conversation_id': conversation_id,
                            'file_id': conversation_data.get('file_id', ''),
                            'file_name': file_name,
                            'question': conversation_data.get('question', ''),
                            'answer': conversation_data.get('answer', ''),
                            'timestamp': conversation_data.get('timestamp', '')
                        })

            return matching_conversations

        except Exception as e:
            current_app.logger.error(
                f"Error searching conversations: {str(e)}")
            return []
