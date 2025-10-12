from pandas.api.types import (
    is_integer_dtype,
    is_float_dtype,
    is_string_dtype,
    is_bool_dtype, 
    is_datetime64_any_dtype, 
    is_timedelta64_dtype
)

def simplify_dtype(dtype):
    if is_integer_dtype(dtype):
        return "int"
    elif is_float_dtype(dtype):
        return "float"
    elif is_bool_dtype(dtype):
        return "bool"
    elif is_datetime64_any_dtype(dtype):
        return "datetime"
    elif is_timedelta64_dtype(dtype):
        return "timedelta"
    elif is_string_dtype(dtype) or dtype == object:
        return "str"
    elif dtype == "pd.DataFrame" or dtype == "pd.Series":
        return dtype
    else:
        return "str"