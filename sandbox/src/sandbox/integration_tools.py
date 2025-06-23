import json
import httpx
import pandas as pd
from io import StringIO
from .secrets import API_URL


def submit_restructured_data(
        df: pd.DataFrame,
        metadata: pd.DataFrame,
        mapping_dict: dict,
        data_description: str,
        dataset_name: str,
        data_modality: str,
        index_first_level: str,
        index_second_level: str | None,
        api_key: str,
        job_id: str) -> dict:

    url = f"{API_URL}/integration/restructured-data"
    header = {"X-API-Key": api_key}

    # Convert DataFrame to CSV string in memory
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_str = csv_buffer.getvalue()
    csv_buffer.close()

    metadata_buffer = StringIO()
    metadata.to_csv(metadata_buffer, index=False)
    metadata_str = metadata_buffer.getvalue()
    metadata_buffer.close()

    mapping_str = json.dumps(mapping_dict)

    try:
        response = httpx.post(
            url,
            files={"data": ("data.csv", csv_str, "text/csv"),
                   "metadata": ("metadata.csv", metadata_str, "text/csv"),
                   "mapping": ("mapping.json", mapping_str, "application/json")},
            headers=header,
            data={
                "data_description": data_description,
                "dataset_name": dataset_name,
                "data_modality": data_modality,
                "index_first_level": index_first_level,
                "index_second_level": index_second_level,
                "job_id": job_id
            },
            timeout=30
        )

    except Exception as e:
        raise ValueError(f"Failed to submit data: {str(e)}")

    if response.status_code != 200:
        raise ValueError(response.text)

    json_markdown = f"""
    ```json
    {json.dumps(response.json())}
    ```
    """

    return json_markdown
