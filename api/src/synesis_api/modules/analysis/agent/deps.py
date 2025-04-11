import pandas as pd
from pathlib import Path
from dataclasses import dataclass
from synesis_api.modules.ontology.schema import Dataset


@dataclass
class EDADeps:
    data_description: str
    data_type: Dataset
    column_names: str
    data_type: str
    problem_description: str
    api_key: str


@dataclass
class EDADepsBasic(EDADeps):
    df: pd.DataFrame


@dataclass
class EDADepsAdvanced(EDADepsBasic):
    basic_eda: str


@dataclass
class EDADepsIndependent(EDADeps):
    basic_eda: str
    advanced_eda: str
    data_path: Path


@dataclass
class EDADepsTotal(EDADeps):
    basic_eda: str
    advanced_eda: str
    independent_eda: str
    python_code: str
