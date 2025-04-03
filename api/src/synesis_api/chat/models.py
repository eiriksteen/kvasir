from sqlalchemy import Table, Column, String, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, BYTEA
import uuid
from ..database.core import metadata


chat_messages = Table(
    "chat_message",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("conversation_id", UUID(as_uuid=True),
           ForeignKey("conversation.id"), nullable=False),
    Column("role", String, nullable=False),
    Column("content", String, nullable=False),
    Column("created_at", DateTime, nullable=False, default=func.now()),
)


pydantic_messages = Table(
    "pydantic_message",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("conversation_id", UUID(as_uuid=True),
           ForeignKey("conversation.id"), nullable=False),
    Column("message_list", BYTEA, nullable=False)
)


conversations = Table(
    "conversation",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("user_id", UUID(as_uuid=True),
           ForeignKey("users.id"), nullable=False)
)
