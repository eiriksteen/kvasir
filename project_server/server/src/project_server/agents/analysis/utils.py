import uuid
from typing import List, Literal
from datetime import datetime
import json


from project_server.redis import get_redis
from project_server.worker import logger
from synesis_schemas.main_server import (
    Dataset,
    AnalysisResult,
    AnalysisStatusMessage,
)


def simplify_dataset_overview(datasets: List[Dataset]) -> list[dict]:
    """
    Simplify the dataset overview to a list of dictionaries.
    """
    # TODO: Make this work with the new dataset structure
    datasets_overview = []
    for dataset in datasets:
        # this is not completely correct, fix this if we want to keep this simplify approach.
        first_object_group = dataset.object_groups[0]
        feature_list = []
        for feature in first_object_group.features:
            simplified_feature = feature.model_dump(
                include={"name", "unit", "description", "type", "subtype", "scale"})
            feature_list.append(simplified_feature)
        simplified_object_group = first_object_group.model_dump(
            include={"dataset_id", "name", "description", "features", "structure_type", "original_id_name"})

        simplified_object_group["features"] = feature_list
        datasets_overview.append(simplified_object_group)

    return datasets_overview


def get_relevant_metadata_for_prompt(metadata_list: List[dict], datatype: Literal["data_source", "dataset"]) -> str:
    context_part = ""
    if datatype == "data_source":
        for idx, metadata_dict in enumerate(metadata_list):
            context_part += f"""The following is some inforation about data source {idx}:
                This is the path to the data source: '/tmp/data_source_{idx}.csv'
                This is some additional information about the data source: {metadata_dict}\n\n"""
    elif datatype == "dataset":
        for idx, metadata_dict in enumerate(metadata_list):
            if metadata_dict["structure_type"] == "time_series":
                original_id_name = metadata_dict["original_id_name"]
                context_part += f"""The following is some information about dataset {idx}:
                    This is the path to the data: '/tmp/dataset_{idx}.parquet'
                    This is some additional information about the data: {metadata_dict}
                    Also note that the data is a multiindex dataframe. Where the first level is '{original_id_name}' and the second level is 'timestamp' \n\n"""
            else:
                return "Modality not supported yet\n\n"
    return context_part


async def post_update_to_redis(analysis_status_message: AnalysisStatusMessage, run_id: uuid.UUID):
    redis_stream = get_redis()

    message_dict = analysis_status_message.model_dump(mode="json", exclude={"section", "analysis_result"})
    if analysis_status_message.section:
        try:
            message_dict["section"] = analysis_status_message.section.model_dump_json()
        except Exception as e:
            logger.error(f"Error dumping section: {e}")
            raise e
    if analysis_status_message.analysis_result:
        try:
            message_dict["analysis_result"] = analysis_status_message.analysis_result.model_dump_json()
        except Exception as e:
            logger.error(f"Error dumping analysis result: {e}")
            raise e

    try:
        await redis_stream.xadd(str(run_id) + "-analysis-status-message", message_dict)
    except Exception as e:
        logger.error(f"Error posting to redis: {e}")
        raise e