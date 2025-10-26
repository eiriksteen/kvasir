import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from synesis_data_interface.structures.aggregation.schema import RawDataStructure, Column, AggregationOutput
from synesis_data_interface.structures.utils import simplify_dtype


def serialize_dataframe_for_aggregation_object(data: pd.DataFrame) -> RawDataStructure:
    columns = []
    new_index_names = []

    counter = 0
    for idx in data.index.names:
        if idx is None:
            new_index_names.append(f'index_{counter}')
            counter += 1
        else:
            new_index_names.append(idx)

    data.index.names = new_index_names
    data = data.reset_index()

    # Convert any NaN values to None before serializing
    data = pd.DataFrame(
        data=np.where(pd.isna(data), None, data),
        columns=data.columns,
        index=data.index
    )

    for col_name in data.columns:
        col = data[col_name]
        dtype = simplify_dtype(col.dtype)

        if dtype == 'datetime':
            values = pd.Series(col.values).dt.strftime('%Y-%m-%dT%H:%M:%S').to_list()
        else:
            values = col.values.tolist()
        columns.append(Column(name=col_name, value_type=dtype, values=values))

    return RawDataStructure(data=columns)


def serialize_raw_data_for_aggregation_object_for_api(output_data: float | int | str | bool | datetime | timedelta | pd.DataFrame | pd.Series) -> AggregationOutput:
    if isinstance(output_data, float | int | str | bool | datetime | timedelta):
        rwd = AggregationOutput(
            output_data=RawDataStructure(
                {('output_data', type(output_data).__name__): [output_data]}),
        )
        return rwd
    elif isinstance(output_data, pd.DataFrame):
        transformed_output_data = serialize_dataframe_for_aggregation_object(
            output_data)
        return AggregationOutput(
            output_data=transformed_output_data,
        )

    elif isinstance(output_data, pd.Series):
        output_data = output_data.to_frame(
            name=output_data.name if output_data.name is not None else 'series')
        transformed_output_data = serialize_dataframe_for_aggregation_object(
            output_data)
        return AggregationOutput(
            output_data=transformed_output_data,
        )
