import json
import httpx
from io import BytesIO
from .secrets import API_URL


def submit_dataset_to_api(dataset_dict: dict) -> dict:
    """
    Submit a dataset dictionary to the API to create a final dataset.

    Args:
        dataset_dict: Dictionary containing dataset information and dataframes

    Returns:
        dict: Response from the API
    """
    url = f"{API_URL}/ontology/dataset"

    # Prepare metadata
    metadata = {
        "name": dataset_dict["name"],
        "description": dataset_dict["description"],
        "modality": dataset_dict["modality"],
        "primary_object_group": {
            "name": dataset_dict["primary_object_group"]["name"],
            "entity_id_name": dataset_dict["primary_object_group"]["entity_id_name"],
            "description": dataset_dict["primary_object_group"]["description"],
            "structure_type": dataset_dict["primary_object_group"]["structure_type"],
            "dataframes": [
                {
                    "filename": f"primary_{i}.parquet",
                    "structure_type": df_info["structure_type"]
                }
                for i, df_info in enumerate(dataset_dict["primary_object_group"]["dataframes"])
            ]
        },
        "annotated_object_groups": [
            {
                "name": group["name"],
                "entity_id_name": group["entity_id_name"],
                "description": group["description"],
                "structure_type": group["structure_type"],
                "dataframes": [
                    {
                        "filename": f"annotated_{group_idx}_{df_idx}.parquet",
                        "structure_type": df_info["structure_type"]
                    }
                    for df_idx, df_info in enumerate(group["dataframes"])
                ]
            }
            for group_idx, group in enumerate(dataset_dict.get("annotated_object_groups", []))
        ],
        "derived_object_groups": [
            {
                "name": group["name"],
                "entity_id_name": group["entity_id_name"],
                "description": group["description"],
                "structure_type": group["structure_type"],
                "dataframes": [
                    {
                        "filename": f"derived_{group_idx}_{df_idx}.parquet",
                        "structure_type": df_info["structure_type"]
                    }
                    for df_idx, df_info in enumerate(group["dataframes"])
                ]
            }
            for group_idx, group in enumerate(dataset_dict.get("derived_object_groups", []))
        ]
    }

    # Prepare files
    files = []

    # Primary object group dataframes
    for i, df_info in enumerate(dataset_dict["primary_object_group"]["dataframes"]):
        df = df_info["df"]
        buffer = BytesIO()
        df.to_parquet(buffer, index=True)
        buffer.seek(0)
        files.append(
            ("files", (f"primary_{i}.parquet", buffer, "application/octet-stream")))

    # Annotated object groups dataframes
    for group_idx, group in enumerate(dataset_dict.get("annotated_object_groups", [])):
        for df_idx, df_info in enumerate(group["dataframes"]):
            df = df_info["df"]
            buffer = BytesIO()
            df.to_parquet(buffer, index=True)
            buffer.seek(0)
            files.append(
                ("files", (f"annotated_{group_idx}_{df_idx}.parquet", buffer, "application/octet-stream")))

    # Derived object groups dataframes
    for group_idx, group in enumerate(dataset_dict.get("derived_object_groups", [])):
        for df_idx, df_info in enumerate(group["dataframes"]):
            df = df_info["df"]
            buffer = BytesIO()
            df.to_parquet(buffer, index=True)
            buffer.seek(0)
            files.append(
                ("files", (f"derived_{group_idx}_{df_idx}.parquet", buffer, "application/octet-stream")))

    try:
        response = httpx.post(
            url,
            files=files,
            data={"metadata": json.dumps(metadata)},
            timeout=60
        )

        if response.status_code != 200:
            raise ValueError(
                f"API request failed with status {response.status_code}: {response.text}")

        return response.json()

    except Exception as e:
        raise ValueError(f"Failed to submit dataset to API: {str(e)}")
