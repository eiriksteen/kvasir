from project_server.utils import get_data_from_container_from_code


async def test_get_data_from_container_from_code():
    async def test_int():
        python_code = "variable = 12"
        data = await get_data_from_container_from_code(python_code, "variable")
        print("Int test:", data)
        print(type(data))
        print("✅ Int test passed")


    async def test_float1():
        python_code = "variable = 12.34"
        data = await get_data_from_container_from_code(python_code, "variable") 
        print("Float test:", data)
        print(type(data))
        print("✅ Float test passed")

    async def test_float2():
        python_code = """
import numpy as np
variable = np.float64(12.34)"""
        data = await get_data_from_container_from_code(python_code, "variable") 
        print("Float 64 test:", data)
        print(type(data))
        print("✅ Float 64 test passed")

    async def test_string():
        python_code = "variable = 'test string'"
        data = await get_data_from_container_from_code(python_code, "variable")
        print("String test:", data)
        print(type(data))
        print("✅ String test passed")


    async def test_datetime():
        python_code = """
from datetime import datetime
variable = datetime(2023, 1, 1)
    """
        data = await get_data_from_container_from_code(python_code, "variable")
        print("Datetime test:", data)
        print(type(data))
        print("✅ Datetime test passed")


    async def test_timedelta():
        python_code = """
from datetime import timedelta
variable = timedelta(days=1)
    """
        data = await get_data_from_container_from_code(python_code, "variable")
        print("Timedelta test:", data)
        print(type(data))
        print("✅ Timedelta test passed")


    async def test_series():
        python_code = """
import pandas as pd
variable = pd.Series([1, 2, 3], name='test_series')
    """
        data = await get_data_from_container_from_code(python_code, "variable")
        print("Series test:", data)
        print(type(data))
        print("✅ Series test passed")


    async def test_dataframe():
        python_code = """
import pandas as pd
variable = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    """
        data = await get_data_from_container_from_code(python_code, "variable")
        print("DataFrame test:", data)
        print(type(data))
        print("✅ DataFrame test passed")

    async def test_dataframe_mixed_types():
        python_code = """
import pandas as pd
from datetime import datetime
variable = pd.DataFrame({
    'int_col': [1, 2, 3],
    'float_col': [4.5, 5.5, 6.5], 
    'str_col': ['a', 'b', 'c'],
    'bool_col': [True, False, True],
    'date_col': [datetime(2023,1,1), datetime(2023,1,2), datetime(2023,1,3)]
})
    """
        data = await get_data_from_container_from_code(python_code, "variable")
        print("Mixed types DataFrame test:", data)
        print(data.dtypes)
        print("✅ Mixed types DataFrame test passed")

    await test_int()
    await test_float1()
    await test_float2()
    await test_string() 
    await test_datetime()
    await test_timedelta()
    await test_series()
    await test_dataframe()
    await test_dataframe_mixed_types()

async def main():
    print("Running utils tests...")
    print("Running test_get_data_from_container_from_code...")
    await test_get_data_from_container_from_code()
    print("✅ utils tests passed")
    print("-"*100, "\n\n")



if __name__ == "__main__":
    import asyncio
    asyncio.run(main())