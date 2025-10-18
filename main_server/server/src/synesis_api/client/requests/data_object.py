import uuid
from datetime import datetime

from synesis_api.client import MainServerClient
from synesis_data_structures.time_series.schema import TimeSeries
from synesis_data_structures.base_schema import AggregationOutput
from synesis_schemas.project_server import AggregationObjectPayloadDataRequest


async def get_time_series_data(client: MainServerClient, time_series_id: uuid.UUID, start_date: datetime, end_date: datetime) -> TimeSeries:
    response = await client.send_request("get", f"/data-object/time-series-data/{time_series_id}", data={"start_date": start_date, "end_date": end_date})
    return TimeSeries(**response.body)

async def get_aggregation_object_payload_data_by_code(client: MainServerClient, data: AggregationObjectPayloadDataRequest) -> AggregationOutput:
    response = await client.send_request("get", f"/data-object/aggregation-object-data", data=data.model_dump_json(), headers={"Content-Type": "application/json"})

    # convert response.body to AggregationOutput as http does not support tuples in json
    aggregation_object_dict = response.body
    aggregation_object_dict["output_data"]["data"] = {tuple(k.split(',')): v for k, v in aggregation_object_dict["output_data"]["data"].items()}
    aggregation_object = AggregationOutput(**aggregation_object_dict)
    return aggregation_object