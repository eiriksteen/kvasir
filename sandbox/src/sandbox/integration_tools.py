import httpx
import pandas as pd
from io import StringIO
from .secrets import API_URL


def submit_restructured_data(
        df: pd.DataFrame,
        data_description: str,
        dataset_name: str,
        data_modality: str,
        index_first_level: str,
        index_second_level: str | None,
        api_key: str) -> dict:

    url = f"{API_URL}/data/restructured_data"
    header = {"X-API-Key": api_key}

    # Convert DataFrame to CSV string in memory
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_str = csv_buffer.getvalue()
    csv_buffer.close()

    try:

        response = httpx.post(
            url,
            files={"file": ("data.csv", csv_str, "text/csv")},
            headers=header,
            data={
                "data_description": data_description,
                "dataset_name": dataset_name,
                "data_modality": data_modality,
                "index_first_level": index_first_level,
                "index_second_level": index_second_level
            }
        )

    except Exception as e:
        raise ValueError(f"Failed to submit data: {str(e)}")

    if response.status_code != 200:
        raise ValueError(response.text)

    json_markdown = f"""
    ```json
    {response.json()}
    ```
    """

    return json_markdown
