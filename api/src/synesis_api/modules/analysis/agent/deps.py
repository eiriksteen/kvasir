import pandas as pd
from pathlib import Path
from dataclasses import dataclass
from synesis_api.modules.ontology.schema import Dataset
from synesis_api.modules.analysis.schema import AnalysisPlan
from typing import List, Literal


@dataclass
class AnalysisPlannerDeps:
    datasets: List[Dataset]
    column_names: str
    problem_description: str
    tools: List[str]


@dataclass
class AnalysisExecutionDeps:
    df: pd.DataFrame
    analysis_plan: AnalysisPlan

