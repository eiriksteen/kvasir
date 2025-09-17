from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class PeriodicScheduleInDB(BaseModel):
    id: UUID
    pipeline_id: UUID
    start_time: datetime
    end_time: datetime
    schedule_description: str
    cron_expression: str
    created_at: datetime
    updated_at: datetime


# Not yet supported
# Would need to have the SWE agent create a script to listen for the event, then deploy it at some frequency
class OnEventScheduleInDB(BaseModel):
    id: UUID
    pipeline_id: UUID
    event_listener_script_path: str
    event_description: str
    created_at: datetime
    updated_at: datetime
