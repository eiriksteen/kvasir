import uuid
from datetime import datetime

from synesis_api.client import MainServerClient
from synesis_data_structures.time_series.schema import TimeSeries
from synesis_data_structures.base_schema import AggregationOutput


async def get_time_series_data(client: MainServerClient, time_series_id: uuid.UUID, start_date: datetime, end_date: datetime) -> TimeSeries:
    response = await client.send_request("get", f"/data-object/time-series-data/{time_series_id}", data={"start_date": start_date, "end_date": end_date})
    return TimeSeries(**response.body)

async def get_aggregation_object_payload_data_by_analysis_result_id(client: MainServerClient, analysis_object_id: uuid.UUID, analysis_result_id: uuid.UUID) -> AggregationOutput:
    response = await client.send_request("get", f"/data-object/aggregation-object-data/{analysis_object_id}/{analysis_result_id}")
    return AggregationOutput(**response.body)