import copy
from dataclasses import dataclass
from pydantic_ai import RunContext
from pydantic_ai.messages import ModelMessage, ModelRequest, UserPromptPart
from typing import Literal, Union

from synesis_api.modules.orchestrator.agent.deps import OrchestratorAgentDeps


@dataclass
class Pattern:
    start_pattern: Literal["<begin_context>",
                           "<begin_project_graph>", "<begin_run_status>"]
    end_pattern: Literal["</begin_context>",
                         "</begin_project_graph>", "</begin_run_status>"]


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
                    if pattern.start_pattern in part.content:
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

    # print(f"MESSAGES BEFORE: \n\n{'\n\n'.join([str(m) for m in messages])}")

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
                    if pattern.start_pattern in part.content:
                        if original_index < last_idx:
                            start_idx = part.content.find(
                                pattern.start_pattern)
                            end_idx = part.content.find(pattern.end_pattern)

                            if start_idx != -1 and end_idx != -1:
                                before = part.content[:start_idx +
                                                      len(pattern.start_pattern)]
                                after = part.content[end_idx:]
                                part.content = before + "\n" + replacement_content + "\n" + after
                                updated_message.parts[idx] = part
                                parts_modified = True

        if parts_modified:
            message_to_add = updated_message

        updated_messages.append(message_to_add)

    updated_messages = updated_messages[::-1]

    # print("LENGTHS"*10)
    # print("conversation id", ctx.deps.conversation_id)
    # print(len(updated_messages))
    # print(len(messages))
    # print("LENGTHS"*10)

    # print(
    #     f"MESSAGES AFTER: \n\n{'\n\n'.join([str(m) for m in updated_messages])}")

    return updated_messages


def keep_only_most_recent_context(
    ctx: RunContext[OrchestratorAgentDeps],
    messages: list[ModelMessage]
) -> list[ModelMessage]:
    """
    Keep only the most recent context in the history.
    """
    pattern = Pattern(start_pattern="<begin_context>",
                      end_pattern="</begin_context>")
    return keep_only_most_recent_by_pattern(ctx, messages, pattern, "[Previous context omitted]")


def keep_only_most_recent_project_graph(
    ctx: RunContext[OrchestratorAgentDeps],
    messages: list[ModelMessage]
) -> list[ModelMessage]:
    """
    Keep only the most recent project graph in the history.
    """
    # assert False, "Messages: \n\n" + "\n\n".join([str(m) for m in messages])
    pattern = Pattern(start_pattern="<begin_project_graph>",
                      end_pattern="</begin_project_graph>")
    return keep_only_most_recent_by_pattern(ctx, messages, pattern, "[Previous project graph omitted]")


def keep_only_most_recent_run_status(
    ctx: RunContext[OrchestratorAgentDeps],
    messages: list[ModelMessage]
) -> list[ModelMessage]:
    """
    Keep only the most recent run status in the history.
    """
    pattern = Pattern(start_pattern="<begin_run_status>",
                      end_pattern="</begin_run_status>")
    return keep_only_most_recent_by_pattern(ctx, messages, pattern, "[Previous run status omitted]")
