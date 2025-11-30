from dataclasses import dataclass

from kvasir_agents.agents.v1.base_agent import AgentDeps


@dataclass(kw_only=True)
class KvasirV1Deps(AgentDeps):
    pass
