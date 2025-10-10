from typing import List, Union, Literal
import uuid
import time
from datetime import datetime


from project_server.redis import get_redis
from synesis_schemas.main_server import (
    DatasetFullWithFeatures, 
    DatasetFull, 
    AnalysisResult,
    AnalysisStatusMessage
)

def simplify_dataset_overview(datasets: List[Union[DatasetFullWithFeatures, DatasetFull]]) -> list[dict]:
    """
    Simplify the dataset overview to a list of dictionaries.
    """
    # TODO: Make this work with the new dataset structure
    datasets_overview = []
    for dataset in datasets:
        first_object_group = dataset.object_groups[0] # this is not completely correct, fix this if we want to keep this simplify approach.
        feature_list = []
        for feature in first_object_group.features:
            simplified_feature = feature.model_dump(include={"name", "unit", "description", "type", "subtype", "scale"})
            feature_list.append(simplified_feature)
        simplified_object_group = first_object_group.model_dump(include={"dataset_id", "name", "description", "features", "structure_type", "original_id_name"})

        simplified_object_group["features"] = feature_list
        datasets_overview.append(simplified_object_group)

    return datasets_overview


def get_relevant_metadata_for_prompt(metadata_list: list[dict], datatype: Literal["data_source", "dataset"]) -> str:
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

async def post_analysis_result_to_redis(message: AnalysisResult, run_id: uuid.UUID):
    redis_stream = get_redis()
    
    analysis_status_message = AnalysisStatusMessage(
        id=uuid.uuid4(),
        run_id=run_id,
        result=message,
        created_at=datetime.now()
    )

    message_dict = analysis_status_message.model_dump(mode="json")
    message_dict['result'] = message.model_dump_json()
    await redis_stream.xadd(str(run_id) + "-result", message_dict)

async def simulate_streaming_output(output: AnalysisResult, run_id: uuid.UUID) -> str:
    """
    Simulate a streaming output by adding a delay between each character.
    """
    streamed_analysis_result = AnalysisResult(**output.model_dump())
    streamed_analysis_result.analysis = ""
    streamed_analysis_result.python_code = ""
    index = 0
    while streamed_analysis_result.analysis != output.analysis:
        if index < len(output.analysis):
            streamed_analysis_result.analysis = output.analysis[:index]
        else:
            streamed_analysis_result.analysis = output.analysis
        if index < len(output.python_code):
            streamed_analysis_result.python_code = output.python_code[:index]
        else:
            streamed_analysis_result.python_code = output.python_code
        index += 5
        await post_analysis_result_to_redis(streamed_analysis_result, run_id)
        time.sleep(0.01)


# def simplify_datasource_overview(datasources: DetailedDataSourceRecords) -> list[dict]:
#     # Datasource object is already simplified now, so this function is not needed anymore.
#     """
#     Simplify the dataset overview to a list of dictionaries.
#     """
#     datasource_overview = []
#     for datasource in datasources:
#         primary_object_group = datasource
#         feature_list = []
#         for feature in datasource.features:
#             simplified_feature = feature.model_dump(include={"name", "unit", "description", "type", "subtype", "scale"})
#             feature_list.append(simplified_feature)
#         simplified_object_group = primary_object_group.model_dump(include={"id", "type", "file_type", "num_rows", "num_columns"})

#         simplified_object_group["features"] = feature_list
#         datasource_overview.append(simplified_object_group)

#     return datasource_overview
