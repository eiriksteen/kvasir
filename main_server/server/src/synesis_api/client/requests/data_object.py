import uuid
from datetime import datetime

from synesis_api.client import MainServerClient
from synesis_data_structures.time_series.schema import TimeSeries


async def get_time_series_data(client: MainServerClient, time_series_id: uuid.UUID, start_date: datetime, end_date: datetime) -> TimeSeries:
    response = await client.send_request("get", f"/data-object/time-series-data/{time_series_id}", data={"start_date": start_date, "end_date": end_date})
    return TimeSeries(**response.body)
