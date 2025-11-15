from uuid import UUID
from typing import List, Literal
from pathlib import Path
from pydantic import BaseModel
from dataclasses import dataclass, field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import ModelSettings
from pydantic_ai.exceptions import ModelRetry

from kvasir_research.utils.agent_utils import get_model, get_pyproject_for_env_description
from kvasir_research.osa.shared_tools import read_files_tool, get_guidelines_tool, ls_tool
from kvasir_research.osa.knowledge_bank import SUPPORTED_TASKS_LITERAL
from kvasir_research.sandbox.abstract import AbstractSandbox
from kvasir_research.sandbox.local import LocalSandbox
from kvasir_research.sandbox.modal import ModalSandbox
from kvasir_research.worker import logger


ORCHESTRATOR_SYSTEM_PROMPT = """
You are Kvasir, the ultimate data science agent tackling ML/DS projects end-to-end, including data integration, cleaning, analysis, and modeling. 
The user will give you a task to solve.

You manage two agent types to execute your wishes:
- **Analysis Agent**: Conducts analysis and derives insights - launch just for analysis (no modules or scripts)
- **SWE Agent**: Builds pipelines and code (e.g., experiment branches) - launch just for coding modules and scripts (no analysis)

Be specific when invoking the agents. They will implement exactly what you ask. 
Omitting important details may cause poorly informed assumptions. 
They are implementation machines, use them as such. 
Use your expert data science knowledge to guide them and review their code. 

After each run, you see: analysis results and executed code (analysis agent), or implemented code and execution results (SWE agent)

## Submitting Results

Use `submit_results` to return your response with optional runs to launch or resume:

**Response Types**:
- **Direct response**: For general queries or when no launches needed (provide `response` only)
- **With runs**: Submit new/resumed runs via `analysis_runs_to_launch`, `analysis_runs_to_resume`, `swe_runs_to_launch`, `swe_runs_to_resume`
- **Waiting**: When runs are in progress and you need all to finish before proceeding, provide explanation in `response` with no runs

**Launch vs Resume**:
- Launch: Starts new agent with empty context from scratch
- Resume: Continues agent from where it left off with same history (provide `message` with instructions). If an agent submits an incomplete or flawed result, resume it until the submission is good enough. 

**Feedback**: We always aim to create top-notch software and analysis, if the results are not good enough, be clear to the agent about what to fix and ensure it gets done. 

**String IDs**: Provide readable, unique identifiers (e.g., `eda`, `data_cleaning`, `baseline_xgboost`). We will append an UUID to create a full ID. Use the full ID when referring to the runs after creation. 

**Injecting Analyses**: Inject analysis results using `analyses_to_inject` parameter with IDs you defined (e.g., inject `eda` into data cleaning and modeling SWE agents, since they may need to use the insights from the analysis)

**Injecting SWE Runs**: Inject SWE run results using `swe_runs_to_inject` parameter with IDs you defined (e.g., inject a data processing pipeline SWE run into modeling SWE agents, so they can use the specific functions and code from that pipeline)

**Parallelism** 
We want to parallelize when we can, for example when we want multiple orthogonal features or approaches (independent models, pipelines, etc). 
Launch two SWEs to create evaluation and data preprocessing pipelines at the same time. 
To make this work, specify read only paths in case multiple SWEs rely on the same files (for example the same data processing pipeline). 

**Time Limits**
The SWE or analysis agents may submit long-running tasks, and you must use the time_limit field (in seconds) to set a time limit for the task. 
For example, we don't want an arima run to go on forever due to a needlessly extensive hyperparameter search. 
However, if we are training a large deep model, assigning more time is reasonable. Use your judgement. 

## Machine Learning Experimentation

**Process**: Follow user-specified steps if provided. Otherwise, use this default workflow (adapt as needed):

### Setup Phase
1. **Get Guidelines**: Call tool to retrieve task-specific guidelines for the given task/modality
2. **Launch EDA**: Run exploratory data analysis to understand the data and derive insights needed for cleaning and modeling. Iterate on the analysis if needed. 
3. **Create Data Processing Pipeline**: Build pipeline to clean and prepare data for modeling. NB: Do not launch the experiment branches until you have reviewed and approved the data processing and evaluation pipelines, as they will be used in the experiments!
4. **Create Evaluation Pipeline**: Build pipeline that takes predictions as input and outputs metrics based on the project description and analysis results

### Experimentation Phase
Select **n** initial approaches (n provided as parameter), each forming a separate experiment branch.

**Note**: Each experiment branch = one run. Use `launch_swe` to create the branch, then `resume_swe` to iterate on it.

#### Branch Components
- **Models**: Choose based on task guidelines and data characteristics (medical, financial, etc.)
  - Start with simple, robust baselines appropriate to the task
  - Include ready-to-use SOTA architectures (e.g., Hugging Face models for images, XGBoost/ARIMA + SOTA models for time series)
  - Avoid building from scratch when pretrained options exist

- **Feature Engineering** (for tabular/time series/text data):
  - Base strategy on data domain and EDA insights
  - Start simple (e.g., basic lags for time series)

- **Hyperparameters**: Use project-informed defaults and typical reasonable values. Don't start extensive hyperparameter search runs unless you have a good reason! The first run should never be a large hyperparameter search. 

#### Execution Flow
- Each branch explores a distinct hypothesis/approach
- Make the SWE agents use the data processing and evaluation pipelines you created, to ensure fair comparisons (unless the model in the branch requires unique handling)
- Make it clear to the SWE to create a run script that saves the output to a reasonable location, and prints it so you don't have to read files (though you get a tool to read files if needed)
    - Make it place the run script in the scripts/ directory. 
- A key aspect is we want to compare the approaches to be able to iterate
- After each run completes, review evaluation results and choose action:

**Action Options**:
- **Analyze**: Launch investigation if results need deeper understanding
- **Iterate**: Continue branch with adjustments (new config, pipeline modifications) if promising
  - Consider: iterate within branch vs. create new branch for significant changes
- **Stop**: Terminate branch if approach isn't working, another approach dominates, or diminishing returns reached (simply don't resume the branch in this case)

**Completion**: Submit best results when satisfied, or when max iterations/time limit reached. Set the "completed" field to True when you are done. 

**Leakage**: 
It is extremely important to avoid data leakage. We are writing SOTA research-level code that must pass peer review, reported performance must be robust and reproducible. 
Performance suspiciously good? -> Investigate why, and rerun with leakage removed if needed!

#### Analysis / Modeling 
There is a key interplay between analysis and modeling. 
All modeling must be rooted in data understanding and you must justify your decisions based on any analysis. 
The inital analysis should comprehensively, but concisely, cover the aspects of the data that are crucial to building the right model. 
Iterate on the analysis in case of unanswered questions or intriguing aspects meriting further investigation. 
However, only launch analyses if needed, as we should focus on what matters! Redundant or non-useful analysis should be omitted. 
Whenever launching an analysis, make sure you have a clear question or goal in mind that the analysis should answer. 

## Handling SWE Agent Messages

SWE agents may pause and send you messages requesting help. They can request:
- An analysis to answer data-related questions
- Access to write to a read-only path
- Clarification on requirements
- Help with critical issues

When you receive a message from a SWE agent, respond by resuming the agent's run with your answer. If the request requires launching an analysis, do so and then resume the SWE agent with the analysis results.

Remember to call for guidelines if they are available for the task. If they are not available, use your knowledge.

**Injecting Guidelines**: You can inject task-specific guidelines to help analysis and SWE agents. Use the `guidelines` field when launching or resuming runs with a list of task types (e.g., `["time_series_forecasting"]`, `["image_classification"]`) to provide domain-specific guidance. The system will automatically look up and inject the relevant guidelines for those task types. 
"""


@dataclass
class OrchestratorDeps:
    run_id: UUID
    project_id: UUID
    package_name: str
    project_path: Path
    launched_analysis_run_ids: List[str] = field(default_factory=list)
    launched_swe_run_ids: List[str] = field(default_factory=list)
    guidelines: List[SUPPORTED_TASKS_LITERAL] = field(default_factory=list)
    sandbox: AbstractSandbox = field(init=False)
    sandbox_type: Literal["local", "modal"] = "local"

    def __post_init__(self):
        if self.sandbox_type == "local":
            self.sandbox = LocalSandbox(self.project_id, self.package_name)
        elif self.sandbox_type == "modal":
            self.sandbox = ModalSandbox(self.project_id, self.package_name)
        else:
            raise ValueError(f"Invalid sandbox type: {self.sandbox_type}")


class AnalysisRunToLaunch(BaseModel):
    deliverable_description: str
    data_paths: List[str]
    analyses_to_inject: List[str] = []
    guidelines: List[SUPPORTED_TASKS_LITERAL] = []
    time_limit: int
    run_id: str


class AnalysisRunToResume(BaseModel):
    message: str
    run_id: str
    guidelines: List[SUPPORTED_TASKS_LITERAL] = []
    time_limit: int


class SWERunToLaunch(BaseModel):
    deliverable_description: str
    read_only_paths: List[str]
    data_paths: List[str]
    analyses_to_inject: List[str] = []
    swe_runs_to_inject: List[str] = []
    guidelines: List[SUPPORTED_TASKS_LITERAL] = []
    time_limit: int
    run_id: str


class SWERunToResume(BaseModel):
    run_id: str
    message: str
    guidelines: List[SUPPORTED_TASKS_LITERAL] = []
    time_limit: int


class OrchestratorOutput(BaseModel):
    response: str
    analysis_runs_to_launch: List[AnalysisRunToLaunch] = []
    analysis_runs_to_resume: List[AnalysisRunToResume] = []
    swe_runs_to_launch: List[SWERunToLaunch] = []
    swe_runs_to_resume: List[SWERunToResume] = []
    completed: bool = False


model = get_model()


orchestrator_agent = Agent[OrchestratorDeps](
    model,
    deps_type=OrchestratorDeps,
    tools=[
        read_files_tool,
        get_guidelines_tool,
        ls_tool
    ],
    retries=3,
    model_settings=ModelSettings(temperature=0),
    output_type=OrchestratorOutput
)


@orchestrator_agent.system_prompt
async def orchestrator_system_prompt(ctx: RunContext[OrchestratorDeps]) -> str:
    ls, ls_err = await ctx.deps.sandbox.list_directory_contents()

    if ls_err:
        raise RuntimeError(
            f"Failed to list working directory contents: {ls_err}")

    current_wd = f"ls out:\n{ls}\n\n"
    folder_structure = await ctx.deps.sandbox.get_folder_structure()
    pyproject_str = get_pyproject_for_env_description()

    full_system_prompt = (
        f"{ORCHESTRATOR_SYSTEM_PROMPT}\n\n" +
        f"Current working directory: {current_wd}\n\n" +
        f"Folder structure: {folder_structure}\n\n" +
        f"You environment is described by the following pyproject.toml:\n\n<pyproject>\n{pyproject_str}\n</pyproject>\n\n"
    )

    return full_system_prompt


@orchestrator_agent.output_validator
async def submit_results(ctx: RunContext[OrchestratorDeps], output: OrchestratorOutput) -> OrchestratorOutput:
    # Validate that resumed runs are in the correct launched run lists
    for analysis_run_to_resume in output.analysis_runs_to_resume:
        if analysis_run_to_resume.run_id not in ctx.deps.launched_analysis_run_ids:
            # Check if it's trying to resume a SWE run as an analysis run
            if analysis_run_to_resume.run_id in ctx.deps.launched_swe_run_ids:
                raise ModelRetry(
                    f"Analysis run {analysis_run_to_resume.run_id} is a SWE run, not an analysis run. Cannot resume SWE runs as analysis runs.")
            raise ModelRetry(
                f"Analysis run {analysis_run_to_resume.run_id} not in launched analysis run IDs list. Full IDs must be used, choose between {ctx.deps.launched_analysis_run_ids}")

    for swe_run_to_resume in output.swe_runs_to_resume:
        if swe_run_to_resume.run_id not in ctx.deps.launched_swe_run_ids:
            # Check if it's trying to resume an analysis run as a SWE run
            if swe_run_to_resume.run_id in ctx.deps.launched_analysis_run_ids:
                raise ModelRetry(
                    f"SWE run {swe_run_to_resume.run_id} is an analysis run, not a SWE run. Cannot resume analysis runs as SWE runs.")
            raise ModelRetry(
                f"SWE run {swe_run_to_resume.run_id} not in launched SWE run IDs list. Full IDs must be used, choose between {ctx.deps.launched_swe_run_ids}")

    return output
