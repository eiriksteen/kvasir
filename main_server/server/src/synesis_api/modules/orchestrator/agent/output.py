import uuid
from typing import Optional, List
from pydantic import model_validator, BaseModel


class ChatHandoffOutput(BaseModel):
    pass


class AnalysisHandoffOutput(BaseModel):
    run_name: str
    dataset_ids: Optional[List[uuid.UUID]] = None
    data_source_ids: Optional[List[uuid.UUID]] = None

    @model_validator(mode="after")
    def validate_dataset_ids(self) -> "AnalysisHandoffOutput":
        if self.dataset_ids is not None:
            assert self.data_source_ids is not None, "Data source IDs are required when dataset IDs are provided"
        return self

    @model_validator(mode="after")
    def validate_data_source_ids(self) -> "AnalysisHandoffOutput":
        if self.data_source_ids is not None:
            assert self.dataset_ids is not None, "Dataset IDs are required when data source IDs are provided"
        return self


class PipelineHandoffOutput(BaseModel):
    run_name: str
    dataset_ids: List[uuid.UUID]
    model_ids: Optional[List[uuid.UUID]] = None

    @model_validator(mode="after")
    def validate_dataset_ids(self) -> "PipelineHandoffOutput":
        assert len(self.dataset_ids) > 0, "One or more dataset IDs are required"
        return self


class DataIntegrationHandoffOutput(BaseModel):
    run_name: str
    data_source_ids: List[uuid.UUID] = []
    # For input datasets
    dataset_ids: List[uuid.UUID] = []

    @model_validator(mode="after")
    def validate_data_source_ids(self) -> "DataIntegrationHandoffOutput":
        assert len(
            self.data_source_ids) > 0 or len(self.dataset_ids) > 0, "One or more data source IDs or dataset IDs are required"
        return self


class ModelIntegrationHandoffOutput(BaseModel):
    run_name: str
    source_id: Optional[uuid.UUID] = None
