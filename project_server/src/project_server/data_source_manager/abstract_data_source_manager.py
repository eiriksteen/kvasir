import uuid
import json
import aiohttp
import pandas as pd
from io import BytesIO
from pathlib import Path
from typing import Union, List
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from fastapi import UploadFile
from project_server.secrets import MAIN_SERVER_URL
from synesis_data_structures.time_series.df_dataclasses import (
    TimeSeriesStructure,
    TimeSeriesAggregationStructure,
    MetadataStructure,
    TimeSeriesAggregationMetadataStructure,
    DatasetStructure
)


@dataclass
class DataSourceCreate:
    pass


class AbstractDataSourceManager(ABC):

    async def _upload_raw_data_metadata_to_main_server(self) -> None:
        pass

    @abstractmethod
    def add_file_data_source(self, file_name: str) -> None:
        """
        - Upload metadata to main server and directly upload raw file to local / s3 storage
        """

    @abstractmethod
    def read_df_from_data_source(self, file_id: uuid.UUID) -> pd.DataFrame:
        """
        - Read df from raw file. This assumes some kinda tabular file, will build other functions for other file types
        """
