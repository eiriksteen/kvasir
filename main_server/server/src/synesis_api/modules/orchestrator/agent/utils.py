import uuid
from pydantic_ai.messages import ModelMessage, ModelRequest, UserPromptPart, ModelResponse, TextPart
from pydantic_ai.exceptions import UnexpectedModelBehavior

from synesis_schemas.main_server import ChatMessage


def to_chat_message(m: ModelMessage, id: uuid.UUID, conversation_id: uuid.UUID) -> ChatMessage:

    first_part = m.parts[0]
    if isinstance(m, ModelRequest):
        if isinstance(first_part, UserPromptPart):
            assert isinstance(first_part.content, str)
            return {
                "id": str(id),
                "conversation_id": str(conversation_id),
                "role": "user",
                "created_at": first_part.timestamp.isoformat(),
                "content": first_part.content,
            }

    elif isinstance(m, ModelResponse):
        if isinstance(first_part, TextPart):
            return {
                "id": str(id),
                "conversation_id": str(conversation_id),
                "role": "assistant",
                "created_at": m.timestamp.isoformat(),
                "content": first_part.content,
            }

    raise UnexpectedModelBehavior(f"Unexpected message type for chat app: {m}")
