import pandas as pd
from pathlib import Path
from dataclasses import dataclass
from synesis_api.modules.ontology.schema import Dataset
from synesis_api.modules.analysis.schema import AnalysisPlan
from typing import List, Literal


@dataclass
class AnalysisDeps:
    df: pd.DataFrame | None = None
