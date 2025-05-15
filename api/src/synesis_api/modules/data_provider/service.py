import pandas as pd
from datetime import datetime, timezone
from uuid import UUID
from pathlib import Path
from fastapi import HTTPException
from synesis_api.modules.data_provider.schema import TimeSeriesData


async def get_time_series_data(
    time_series_id: UUID,
    user_id: UUID,
    start_timestamp: datetime = None,
    end_timestamp: datetime = datetime.now(timezone.utc),
    n_past_values: int = 1024
) -> TimeSeriesData:

    # TODO: proper fetch
    data_path = Path.cwd() / "integrated_data" / \
        user_id / f"{time_series_id}.csv"

    if not data_path.exists():
        raise HTTPException(status_code=404, detail="Time series not found")

    data = pd.read_csv(data_path)

    pass
