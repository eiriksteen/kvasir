import pandas as pd
from dataclasses import dataclass


# Separate metadata structures and raw data structures, since sometimes we want to access the metadata without loading the raw data
@dataclass(kw_only=True)
class MetadataStructure:
    entity_metadata: pd.DataFrame
    feature_information: pd.DataFrame
