import pandas as pd
from pathlib import Path
from dataclasses import dataclass
from ...ontology.schema import DatasetBase


@dataclass
class EDADeps:
    data_description: str
    data_type: DatasetBase
    problem_description: str
    api_key: str


@dataclass
class EDADepsBasic(EDADeps):
    df: pd.DataFrame


@dataclass
class EDADepsAdvanced(EDADepsBasic):
    basic_data_analysis: str


@dataclass
class EDADepsIndependent(EDADeps):
    basic_data_analysis: str
    advanced_data_analysis: str
    data_path: Path


@dataclass
class EDADepsSummary(EDADeps):
    basic_data_analysis: str
    advanced_data_analysis: str
    independent_data_analysis: str
    python_code: str
