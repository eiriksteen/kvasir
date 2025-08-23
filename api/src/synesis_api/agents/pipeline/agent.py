from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

from synesis_api.agents.pipeline.prompt import PIPELINE_AGENT_SYSTEM_PROMPT
from synesis_api.utils.pydanticai_utils import get_model
from synesis_api.agents.pipeline.output import (
    SearchQueryOutput,
    DetailedFunctionDescription,
    ImplementationFeedbackOutput,
    submit_final_pipeline_output,
)
from synesis_data_structures.time_series.definitions import get_data_structures_overview, get_data_structure_description


model = get_model()


pipeline_agent = Agent(
    model,
    system_prompt=PIPELINE_AGENT_SYSTEM_PROMPT,
    model_settings=ModelSettings(temperature=0.0),
    tools=[get_data_structures_overview, get_data_structure_description],
    output_type=[
        SearchQueryOutput,
        DetailedFunctionDescription,
        ImplementationFeedbackOutput,
        submit_final_pipeline_output
    ],
    retries=3
)
