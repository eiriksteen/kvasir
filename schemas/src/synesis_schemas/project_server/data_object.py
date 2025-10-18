from pydantic import BaseModel

class AggregationObjectPayloadDataRequest(BaseModel):
    python_code: str
    output_variable: str