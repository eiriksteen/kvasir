from datetime import datetime, timedelta
import pandas as pd
from rich import print as rich_print
import asyncio
from synesis_data_structures.base_schema import RawDataStructure, AggregationOutput
from synesis_data_structures.utils import simplify_dtype

def serialize_dataframe_for_aggregation_object(data: pd.DataFrame) -> RawDataStructure:
    data_dict = {}
    new_names = []

    counter = 0
    for idx in data.index.names:
        if idx is None:
            new_names.append(f'index_{counter}')
            counter += 1
        else:
            new_names.append(idx)
    data.index.names = new_names
    data = data.reset_index()
    
    for col_name in data.columns:
        col = data[col_name]
        dtype = simplify_dtype(col.dtype)
        
        data_dict[(col.name, dtype)] = col.values.tolist()

    return RawDataStructure(data=data_dict)


def serialize_raw_data_to_aggregation_object_for_api(input_data: pd.DataFrame, output_data: float | int | str | bool | datetime | timedelta | pd.DataFrame | pd.Series) -> AggregationOutput:
    transformed_input_data = serialize_dataframe_for_aggregation_object(input_data)
    if isinstance(output_data, float | int | str | bool | datetime | timedelta):
        rwd = AggregationOutput(
            input_data=transformed_input_data,
            output_data=RawDataStructure(data={('output_data', type(output_data).__name__): [output_data]}),
        )
        return rwd
    elif isinstance(output_data, pd.DataFrame):
        transformed_output_data = serialize_dataframe_for_aggregation_object(output_data)
        return AggregationOutput(
            input_data=transformed_input_data,
            output_data=transformed_output_data,
        )

    elif isinstance(output_data, pd.Series):
        output_data = output_data.to_frame(name='series')
        transformed_output_data = serialize_dataframe_for_aggregation_object(output_data)
        return AggregationOutput(
            input_data=transformed_input_data,
            output_data=transformed_output_data,
        )
    

def test_string_serialization(input_data: pd.DataFrame):
    """Test serialization of string data"""
    print("\n=== Testing String Serialization ===")
    try:
        data = "hei"
        analysis_result_data = serialize_raw_data_to_aggregation_object_for_api(input_data, data)
        rich_print(analysis_result_data)
        print("✅ String Serialization Test PASSED")
    except Exception as e:
        print(f"❌ String Serialization Test FAILED: {e}")


def test_integer_serialization(input_data: pd.DataFrame):
    """Test serialization of integer data"""
    print("\n=== Testing Integer Serialization ===")
    try:
        data = 12
        analysis_result_data = serialize_raw_data_to_aggregation_object_for_api(input_data, data)
        rich_print(analysis_result_data)
        print("✅ Integer Serialization Test PASSED")
    except Exception as e:
        print(f"❌ Integer Serialization Test FAILED: {e}")


def test_float_serialization(input_data: pd.DataFrame):
    """Test serialization of float data"""
    print("\n=== Testing Float Serialization ===")
    try:
        data = 15.3
        analysis_result_data = serialize_raw_data_to_aggregation_object_for_api(input_data, data)
        rich_print(analysis_result_data)
        print("✅ Float Serialization Test PASSED")
    except Exception as e:
        print(f"❌ Float Serialization Test FAILED: {e}")


def test_boolean_serialization(input_data: pd.DataFrame):
    """Test serialization of boolean data"""
    print("\n=== Testing Boolean Serialization ===")
    try:
        data = True
        analysis_result_data = serialize_raw_data_to_aggregation_object_for_api(input_data, data)
        rich_print(analysis_result_data)
        print("✅ Boolean Serialization Test PASSED")
    except Exception as e:
        print(f"❌ Boolean Serialization Test FAILED: {e}")


def test_datetime_serialization(input_data: pd.DataFrame):
    """Test serialization of datetime data"""
    print("\n=== Testing Datetime Serialization ===")
    try:
        data = datetime.now()
        analysis_result_data = serialize_raw_data_to_aggregation_object_for_api(input_data, data)
        rich_print(analysis_result_data)
        print("✅ Datetime Serialization Test PASSED")
    except Exception as e:
        print(f"❌ Datetime Serialization Test FAILED: {e}")


def test_timedelta_serialization(input_data: pd.DataFrame):
    """Test serialization of timedelta data"""
    print("\n=== Testing Timedelta Serialization ===")
    try:
        data = timedelta(days=1)
        analysis_result_data = serialize_raw_data_to_aggregation_object_for_api(input_data, data)
        rich_print(analysis_result_data)
        print("✅ Timedelta Serialization Test PASSED")
    except Exception as e:
        print(f"❌ Timedelta Serialization Test FAILED: {e}")


def test_dataframe_serialization(input_data: pd.DataFrame):
    """Test serialization of regular DataFrame"""
    print("\n=== Testing DataFrame Serialization ===")
    try:
        data = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        analysis_result_data = serialize_raw_data_to_aggregation_object_for_api(input_data, data)
        rich_print(analysis_result_data)
        print("✅ DataFrame Serialization Test PASSED")
    except Exception as e:
        print(f"❌ DataFrame Serialization Test FAILED: {e}")


def test_multiindex_dataframe_serialization(input_data: pd.DataFrame):
    """Test serialization of DataFrame with MultiIndex"""
    print("\n=== Testing MultiIndex DataFrame Serialization ===")
    try:
        arrays = [['A', 'A', 'B', 'B'], [1, 2, 1, 2]]
        index = pd.MultiIndex.from_arrays(arrays, names=('letter', 'number'))
        data = pd.DataFrame({'value': [100, 200, 300, 400]}, index=index)
        analysis_result_data = serialize_raw_data_to_aggregation_object_for_api(input_data, data)
        rich_print(analysis_result_data)
        print("✅ MultiIndex DataFrame Serialization Test PASSED")
    except Exception as e:
        print(f"❌ MultiIndex DataFrame Serialization Test FAILED: {e}")


def test_series_serialization(input_data: pd.DataFrame):
    """Test serialization of pandas Series"""
    print("\n=== Testing Series Serialization ===")
    try:
        data = pd.Series([1, 2, 3])
        analysis_result_data = serialize_raw_data_to_aggregation_object_for_api(input_data, data)
        rich_print(analysis_result_data)
        print("✅ Series Serialization Test PASSED")
    except Exception as e:
        print(f"❌ Series Serialization Test FAILED: {e}")



async def main():
    example_input_date = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    test_string_serialization(example_input_date)
    test_integer_serialization(example_input_date)
    test_float_serialization(example_input_date)
    test_boolean_serialization(example_input_date)
    test_datetime_serialization(example_input_date)
    test_timedelta_serialization(example_input_date)
    test_dataframe_serialization(example_input_date)
    test_multiindex_dataframe_serialization(example_input_date)
    test_series_serialization(example_input_date)
    

if __name__ == "__main__":
    asyncio.run(main())

    