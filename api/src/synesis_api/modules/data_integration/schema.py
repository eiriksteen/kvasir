from uuid import UUID
from typing import Literal
from datetime import datetime
from synesis_api.base_schema import BaseSchema
from datetime import timezone


class IntegrationJobResult(BaseSchema):
    job_id: UUID
    dataset_id: UUID


class IntegrationJobResultInDB(IntegrationJobResult):
    python_code: str


class IntegrationAgentFeedback(BaseSchema):
    job_id: UUID
    content: str


class DataSubmissionResponse(BaseSchema):
    dataset_id: UUID


class IntegrationAgentState(BaseSchema):
    agent_state: str


class IntegrationPydanticMessage(BaseSchema):
    id: UUID
    job_id: UUID
    message_list: bytes
    created_at: datetime = datetime.now(timezone.utc)


class IntegrationMessage(BaseSchema):
    id: UUID
    job_id: UUID
    content: str
    role: Literal["assistant", "user"]
    type: Literal["tool_call",  # agent calls tool
                  "help_call",  # agent calls human for help
                  "help_response",  # human responds to help call
                  "feedback",  # human provides feedback on the results
                  "intervention",  # human intervenes in the integration job
                  "summary"]  # agent summarizes the integration job
    created_at: datetime = datetime.now(timezone.utc)


class IntegrationJobLocalInput(BaseSchema):
    job_id: UUID
    data_description: str
    data_directory: str
