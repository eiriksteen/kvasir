from typing import Literal
from ..base_schema import BaseSchema


class DataDescription(BaseSchema):
    data_description: str
    data_type: str
    data_format: str
    data_source: str
    data_size: str


class GoalDescription(BaseSchema):
    goal_description: str
    goal_type: Literal["prediction", "automation", "insights", "other"]


class DeliverableDescription(BaseSchema):
    deliverable_description: str
    deliverable_type: Literal["api",
                              "web_app",
                              "report",
                              "periodic_job",
                              "other"]


class ChatSummary(BaseSchema):
    data_description: DataDescription
    goals_description: list[GoalDescription]
    deliverables_description: list[DeliverableDescription]


class ChatbotOutput(BaseSchema):
    state: Literal["in_progress", "done"]
    response: str | None = None
    summary: ChatSummary | None = None
