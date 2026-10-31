"""
CodeSphere - AI Conversation Models
-----------------------------------
Maintains conversational history for the CodeSphere AI Learning Assistant,
recording user queries, AI responses, fallback tags, and timestamps.
"""

from datetime import datetime
from app.extensions import db


class AIConversation(db.Model):
    """
    Chat session initiated by a student with the AI Learning Assistant.
    Supports individual deletion and isolated access control.
    """
    __tablename__ = 'ai_conversations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(150), default='New Learning Session', nullable=False)
    topic = db.Column(db.String(100), default='General Tutoring', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    messages = db.relationship('AIMessage', backref='conversation', cascade='all, delete-orphan', lazy='joined', order_by='AIMessage.timestamp')

    @property
    def message_count(self):
        """Returns total messages in this conversation."""
        return len(self.messages)

    def __repr__(self):
        return f"<AIConversation {self.id} User:{self.user_id} Title:'{self.title}'>"


class AIMessage(db.Model):
    """
    Individual message in an AI conversation.
    Tracks whether a response was generated via OpenAI API or fallback engine.
    """
    __tablename__ = 'ai_messages'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('ai_conversations.id'), nullable=False, index=True)
    sender = db.Column(db.String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = db.Column(db.Text, nullable=False)
    is_fallback = db.Column(db.Boolean, default=False, nullable=False)  # Clearly labels fallback responses
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AIMessage {self.id} Sender:{self.sender} Fallback:{self.is_fallback}>"
