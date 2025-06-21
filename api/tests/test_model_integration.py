from __future__ import annotations as _annotations

import asyncio
import httpx
import redis
from dataclasses import dataclass
from typing import Union, Literal
import sys

from synesis_api.utils import get_model
from synesis_api.secrets import GITHUB_TOKEN
from synesis_api.redis import get_redis
from synesis_api.modules.model_integration.agent.runner import ModelIntegrationRunner

model = get_model()


def get_test_params(use_pip: bool = False):
    if use_pip:
        # Example: XGBoost pip package
        return dict(model_id="xgboost", source="pip", verbose=False)
    else:
        # Test repository URL (using a sample time series ML repository)
        return dict(model_id="https://github.com/kwuking/TimeMixer", source="github", verbose=False)


async def test_model_integration(use_pip: bool = False):
    """Test the ModelIntegrationAgent with a sample repository or pip package."""
    params = get_test_params(use_pip)
    runner = ModelIntegrationRunner(**params)
    output = await runner()

    print("="*20, "MODEL INTEGRATION OUTPUT", "="*20)
    print(output)
    print("="*50)


async def main():
    """Main function to run the test."""
    # Allow toggling via command line: python test_model_integration.py pip
    use_pip = len(sys.argv) > 1 and sys.argv[1].lower() == "pip"
    await test_model_integration(use_pip=use_pip)


if __name__ == "__main__":
    asyncio.run(main())
