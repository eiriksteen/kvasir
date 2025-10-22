import pandas as pd
from typing import List

from synesis_schemas.main_server import Dataset, DataSource
from synesis_data_interface.structures.overview import get_data_structure_description
from synesis_data_interface.sources.overview import get_data_source_description


def get_structure_descriptions_from_datasets(datasets: List[Dataset]) -> str:
    structure_descriptions = {}
    for dataset in datasets:
        for structure in dataset.object_groups:
            structure_type = structure.structure_type
            structure_descriptions[structure_type] = get_data_structure_description(
                structure_type)

    return "\n\n".join(structure_descriptions.values())


def get_data_source_type_descriptions_from_data_sources(data_sources: List[DataSource]) -> str:
    data_source_descriptions = {}
    for data_source in data_sources:
        data_source_descriptions[data_source.type] = get_data_source_description(
            data_source.type)

    return "\n\n".join(data_source_descriptions.values())


def get_basic_df_info(df: pd.DataFrame):
    shape = df.shape
    sample_data = df.head()
    info = df.info()
    description = df.describe()

    return f"Shape: {shape}\nSample Data: {sample_data}\nInfo: {info}\nDescription: {description}"


def get_df_info(df: pd.DataFrame, max_cols: int = 25):
    """
    Returns a string containing basic information about the DataFrame, including the shape, sample data, info, description, and correlation matrix.

    Returns:
        str: A formatted string containing the DataFrame information
    """
    # Initialize list to store output strings
    output = []

    # Base info functions that are always shown
    info_functions = {
        "DATA SHAPE": lambda df: df.shape,
        "SAMPLE DATA": lambda df: df.head(),
        "DATA INFO": lambda df: df.info(),
        "DATA DESCRIPTION": lambda df: df.describe(),
        "DATA CORRELATION": lambda df: df.select_dtypes(include=['int', 'float', 'bool'])[
            df.select_dtypes(
                include=['int', 'float', 'bool']).columns[:max_cols]
        ].corr()
    }

    # Get categorical columns (including potential integer categories)
    categorical_cols = (
        df.select_dtypes(include=['object', 'category']).columns.tolist() +
        [col for col in df.select_dtypes(include=['int', 'int64']).columns
         # columns with less than 5% unique values
         if df[col].nunique() < len(df) * 0.05]
    )

    if len(df.columns) <= max_cols:
        # For smaller datasets, show detailed null percentages and categorical unique counts
        info_functions.update({
            "DATA NULL PERCENTAGES": lambda df: (df.isnull().sum() / len(df)).sort_values(ascending=False),
            "CATEGORICAL UNIQUE VALUES": lambda df: df[categorical_cols].nunique() if len(categorical_cols) > 0 else "No categorical columns found"
        })
    else:
        # For larger datasets, show summary statistics
        def null_stats(df): return pd.Series({
            'min null percentage': (df.isnull().sum() / len(df)).min(),
            'max null percentage': (df.isnull().sum() / len(df)).max(),
            'mean null percentage': (df.isnull().sum() / len(df)).mean()
        })

        def unique_cat_stats(df): return pd.Series({
            'min unique values': df[categorical_cols].nunique().min() if len(categorical_cols) > 0 else "No categorical columns",
            'max unique values': df[categorical_cols].nunique().max() if len(categorical_cols) > 0 else "No categorical columns",
            'mean unique values': df[categorical_cols].nunique().mean() if len(categorical_cols) > 0 else "No categorical columns"
        })

        info_functions.update({
            "NULL VALUE STATISTICS": null_stats,
            "CATEGORICAL UNIQUE VALUE STATISTICS": unique_cat_stats
        })

    for section, func in info_functions.items():
        try:
            output.append(f"[{section}]\n")
            output.append(str(func(df)))
            output.append("\n")  # Add extra newline between sections
        except Exception as e:
            output.append(f"Failed to get {section.lower()}: {e}\n")

    return "".join(output)
