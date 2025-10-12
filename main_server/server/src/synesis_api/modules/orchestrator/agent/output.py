import uuid
from typing import Optional, List
from pydantic import model_validator, BaseModel


class NoHandoffOutput(BaseModel):
    pass


class AnalysisRunDescriptionOutput(BaseModel):
    run_name: str
    plan_and_deliverable_description_for_user: str
    plan_and_deliverable_description_for_agent: str
    questions_for_user: Optional[str] = None
    dataset_ids: List[uuid.UUID] = []
    data_source_ids: List[uuid.UUID] = []

    @model_validator(mode="after")
    def validate_dataset_ids(self) -> "AnalysisRunDescriptionOutput":
        if self.dataset_ids:
            assert self.data_source_ids, "Data source IDs are required when dataset IDs are provided"
        return self

    @model_validator(mode="after")
    def validate_data_source_ids(self) -> "AnalysisRunDescriptionOutput":
        if self.data_source_ids:
            assert self.dataset_ids, "Dataset IDs are required when data source IDs are provided"
        return self


class PipelineRunDescriptionOutput(BaseModel):
    run_name: str
    plan_and_deliverable_description_for_user: str
    plan_and_deliverable_description_for_agent: str
    questions_for_user: Optional[str] = None
    configuration_defaults_description: Optional[str] = None
    input_dataset_ids: List[uuid.UUID]
    input_model_entity_ids: List[uuid.UUID] = []

    @model_validator(mode="after")
    def validate_dataset_ids(self) -> "PipelineRunDescriptionOutput":
        assert len(
            self.input_dataset_ids) > 0, "One or more dataset IDs are required"
        return self


class DataIntegrationRunDescriptionOutput(BaseModel):
    run_name: str
    plan_and_deliverable_description_for_user: str
    plan_and_deliverable_description_for_agent: str
    questions_for_user: Optional[str] = None
    data_source_ids: List[uuid.UUID] = []
    # For input datasets
    dataset_ids: List[uuid.UUID] = []

    @model_validator(mode="after")
    def validate_data_source_ids(self) -> "DataIntegrationRunDescriptionOutput":
        assert len(
            self.data_source_ids) > 0 or len(self.dataset_ids) > 0, "One or more data source IDs or dataset IDs are required"
        return self


class ModelIntegrationRunDescriptionOutput(BaseModel):
    run_name: str
    plan_and_deliverable_description_for_user: str
    plan_and_deliverable_description_for_agent: str
    questions_for_user: Optional[str] = None
