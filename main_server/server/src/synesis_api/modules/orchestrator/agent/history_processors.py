import copy
from dataclasses import dataclass
from pydantic_ai import RunContext
from pydantic_ai.messages import ModelMessage, ModelRequest, UserPromptPart
from typing import Literal, Union

from synesis_api.modules.orchestrator.agent.deps import OrchestratorAgentDeps


@dataclass
class Pattern:
    start: Literal["<context>",
                   "<project_desc>",
                   "<run_status>"]
    end: Literal["</context>",
                 "</project_desc>",
                 "</run_status>"]


CONTEXT_PATTERN = Pattern(
    start="<context>", end="</context>")

PROJECT_DESC_PATTERN = Pattern(
    start="<project_desc>", end="</project_desc>")

RUN_STATUS_PATTERN = Pattern(
    start="<run_status>", end="</run_status>")


def get_last_message_index_by_pattern(messages: list[ModelMessage], pattern: Pattern) -> Union[int, None]:
    """
    Find the index of the last message containing a script modification tool call.
    Returns the index of the ToolCallPart message, not the ToolReturnPart.
    Returns -1 if no script modification is found.
    """

    for i in range(len(messages) - 1, -1, -1):
        message = messages[i]

        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, UserPromptPart):
                    if pattern.start in part.content:
                        return i

    return None


def keep_only_most_recent_by_pattern(
    _: RunContext[OrchestratorAgentDeps],
    messages: list[ModelMessage],
    pattern: Pattern,
    replacement_content: str
) -> list[ModelMessage]:
    """
    Keep only the most recent message by pattern in the history.
    """

    last_idx = get_last_message_index_by_pattern(messages, pattern)

    if last_idx is None:
        return messages

    updated_messages = []

    for i, message in enumerate(messages[::-1]):
        original_index = len(messages) - 1 - i
        message_to_add = message
        updated_message = copy.deepcopy(message)
        parts_modified = False

        if isinstance(message, ModelRequest):
            for idx, part in enumerate(message.parts):
                if isinstance(part, UserPromptPart):
                    if pattern.start in part.content:
                        if original_index < last_idx:
                            start_idx = part.content.find(
                                pattern.start)
                            end_idx = part.content.find(pattern.end)

                            if start_idx != -1 and end_idx != -1:
                                before = part.content[:start_idx +
                                                      len(pattern.start)]
                                after = part.content[end_idx:]
                                part.content = before + "\n" + replacement_content + "\n" + after
                                updated_message.parts[idx] = part
                                parts_modified = True

        if parts_modified:
            message_to_add = updated_message

        updated_messages.append(message_to_add)

    updated_messages = updated_messages[::-1]

    return updated_messages


def keep_only_most_recent_context(
    ctx: RunContext[OrchestratorAgentDeps],
    messages: list[ModelMessage]
) -> list[ModelMessage]:
    """
    Keep only the most recent context in the history.
    """

    return keep_only_most_recent_by_pattern(ctx, messages, CONTEXT_PATTERN, "[Previous context omitted]")


def keep_only_most_recent_project_desc(
    ctx: RunContext[OrchestratorAgentDeps],
    messages: list[ModelMessage]
) -> list[ModelMessage]:
    """
    Keep only the most recent project description in the history.
    """
    # assert False, "Messages: \n\n" + "\n\n".join([str(m) for m in messages])
    return keep_only_most_recent_by_pattern(ctx, messages, PROJECT_DESC_PATTERN, "[Previous project description omitted]")


def keep_only_most_recent_run_status(
    ctx: RunContext[OrchestratorAgentDeps],
    messages: list[ModelMessage]
) -> list[ModelMessage]:
    """
    Keep only the most recent run status in the history.
    """
    return keep_only_most_recent_by_pattern(ctx, messages, RUN_STATUS_PATTERN, "[Previous run status omitted]")
