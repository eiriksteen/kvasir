from pydantic import BaseModel
from typing import Literal


class DataDescription(BaseModel):
    data_description: str
    data_type: str
    data_format: str
    data_source: str
    data_size: str


class GoalDescription(BaseModel):
    goal_description: str
    goal_type: Literal["prediction", "automation", "insights", "other"]


class DeliverableDescription(BaseModel):
    deliverable_description: str
    deliverable_type: Literal["api",
                              "web_app",
                              "report",
                              "periodic_job",
                              "other"]


class ChatSummary(BaseModel):
    data_description: DataDescription
    goals_description: list[GoalDescription]
    deliverables_description: list[DeliverableDescription]


class ChatbotOutput(BaseModel):
    state: Literal["in_progress", "done"]
    response: str | None = None
    summary: ChatSummary | None = None
