from typing import List

from synesis_api.base_schema import BaseSchema


# Schema outputs

class SetupAgentOutput(BaseSchema):
    dependencies: List[str]
    python_version: str


class SetupAgentOutputWithScript(SetupAgentOutput):
    script: str
