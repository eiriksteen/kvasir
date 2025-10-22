from pydantic_ai import Agent, RunContext
from pydantic_ai.settings import ModelSettings

from synesis_api.utils.pydanticai_utils import get_model
from synesis_schemas.main_server.project import EntityPositionCreate


PROJECT_AGENT_SYSTEM_PROMPT = """
You are a helpful assistant that can generate a suitable position for an entity in a project. 
We are working with an entity relationship diagram, and want to place a new entity appropriately in relation to other entities. 
The ERD is modeling a data science project, where we have the following entities:

- Data Sources
- Datasets
- Analyses
- Pipelines
- Models

There are lines showing the data flow between the entities. We have a graph showing the edges, and this you will be provided to ensure you place it appropriately. 

Some guidelines: 
- The origo is the top left corner, so a higher x-position means further to the right, and a higher y-position means further down
- No entites should overlap
- Follow the existing placement convention
    - For example if the data flow goes from left to right, and the new entity has data flowing to the left, it makes sense to place it to the right of the existing entities
- Use commmon sense, what matters is that it looks nice 

The graph will be provided in the user prompt. 
"""


model = get_model()

project_agent = Agent(
    model,
    system_prompt=PROJECT_AGENT_SYSTEM_PROMPT,
    retries=3,
    output_type=EntityPositionCreate
)
