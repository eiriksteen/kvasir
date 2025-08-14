# Synesis Data Structures

This package contains the formalized data structures used throughout the Synesis application.

## Structure

- `src/synesis_data_structures/` - Main package directory
  - `schemas/` - Pydantic schemas for data validation
  - `models/` - Core data models and structures
  - `types/` - Type definitions and custom types
  - `utils/` - Utility functions for data manipulation

## Installation

```bash
pip install -e .
```

## Usage

```python
from synesis_data_structures.schemas import DatasetSchema
from synesis_data_structures.models import Dataset
```

## Development

This package follows the same structure as the main API package for consistency. 