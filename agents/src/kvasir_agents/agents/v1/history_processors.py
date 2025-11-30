import copy
from dataclasses import dataclass
from pydantic_ai import RunContext
from pydantic_ai.messages import ModelMessage, ModelRequest, ToolReturnPart


def get_last_script_message_index(messages: list[ModelMessage]) -> dict[str, int]:
    """
    Find the index of the last message containing a script modification tool call.
    Returns the index of the ToolCallPart message, not the ToolReturnPart.
    Returns -1 if no script modification is found.
    """

    last_idx_per_file_path = {}

    for i in range(len(messages) - 1, -1, -1):
        message = messages[i]

        if isinstance(message, ModelRequest):
            for part in message.parts:
                if "</file>" in part.content:
                    # Extract file path: <file path=path/to/file.py>...
                    path_start = part.content.find("path=")
                    if path_start != -1:
                        path_start += len("path=")
                        path_end = part.content.find(">", path_start)
                        if path_end != -1:
                            file_path = part.content[path_start:path_end].strip(
                            )
                            if file_path and file_path not in last_idx_per_file_path:
                                last_idx_per_file_path[file_path] = i

    return last_idx_per_file_path


async def keep_only_most_recent_script(
        _: RunContext,
        messages: list[ModelMessage]) -> list[ModelMessage]:
    """
    Keep only the most recent script in the history.
    """
    last_idx_per_file_path = get_last_script_message_index(messages)

    if not last_idx_per_file_path:
        # No script modifications found, return messages as is
        return messages

    updated_messages = []

    for i, message in enumerate(messages[::-1]):
        original_index = len(messages) - 1 - i
        message_to_add = message
        updated_message = copy.deepcopy(message)
        parts_modified = False

        if isinstance(message, ModelRequest):
            for idx, part in enumerate(message.parts):
                if isinstance(part, ToolReturnPart):
                    if "</file>" in part.content:
                        # Extract file path: <file path=path/to/file.py>...
                        path_start = part.content.find("path=")
                        if path_start != -1:
                            path_start += len("path=")
                            path_end = part.content.find(">", path_start)
                            if path_end != -1:
                                file_path = part.content[path_start:path_end].strip(
                                )
                                if file_path and file_path in last_idx_per_file_path:
                                    if original_index < last_idx_per_file_path[file_path]:
                                        # This is an older script, omit it
                                        part.content = "Successfully updated the script. The script is not automatically run and validated, you must call the result submission tool to submit the script for validation and feedback."
                                        updated_message.parts[idx] = part
                                        parts_modified = True

        if parts_modified:
            message_to_add = updated_message

        updated_messages.append(message_to_add)

    updated_messages = updated_messages[::-1]

    return updated_messages


@dataclass
class HistoryPattern:
    start: str
    end: str


def get_last_message_index_by_pattern(messages: list[ModelMessage], pattern: HistoryPattern) -> int:
    """
    Find the index of the last message containing a full analysis.
    Returns the index of the ToolReturnPart message containing the analysis.
    Returns -1 if no analysis is found.
    """
    for i in range(len(messages) - 1, -1, -1):
        message = messages[i]

        if isinstance(message, ModelRequest):
            for part in message.parts:
                if pattern.end in part.content:
                    return i

    return -1


async def keep_only_most_recent_by_pattern(
        _: RunContext,
        messages: list[ModelMessage],
        pattern: HistoryPattern) -> list[ModelMessage]:
    """
    Keep only the most recent analysis in the history.
    Older analysis returns are replaced with a simple success message.
    """
    last_message_idx = get_last_message_index_by_pattern(messages, pattern)

    if last_message_idx == -1:
        # No analysis found, return messages as is
        return messages

    updated_messages = []

    for i, message in enumerate(messages):
        message_to_add = message
        updated_message = copy.deepcopy(message)
        parts_modified = False

        if isinstance(message, ModelRequest):
            for idx, part in enumerate(message.parts):
                if pattern.end in part.content:
                    if i < last_message_idx:
                        content = part.content
                        start_idx = content.find(pattern.start)
                        end_idx = content.find(pattern.end)

                        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                            before = content[:start_idx]
                            after = content[end_idx + len(pattern.end):]
                            replacement = f"Old {pattern.start} removed."
                            updated_message.parts[idx].content = before + \
                                replacement + after
                            parts_modified = True
                        elif pattern.end in content:
                            raise RuntimeError(
                                f"Pattern end found without start in message: {content}")

        if parts_modified:
            message_to_add = updated_message

        updated_messages.append(message_to_add)

    return updated_messages


async def keep_only_most_recent_analysis(
        _: RunContext,
        messages: list[ModelMessage]) -> list[ModelMessage]:
    processed_messages = await keep_only_most_recent_by_pattern(
        _, messages, HistoryPattern(start="<analysis", end="</analysis>"))

    return processed_messages


async def keep_only_most_recent_project_description(
        _: RunContext,
        messages: list[ModelMessage]) -> list[ModelMessage]:
    processed_messages = await keep_only_most_recent_by_pattern(
        _, messages, HistoryPattern(start="<project_description", end="</project_description>"))
    return processed_messages


async def keep_only_most_recent_folder_structure(
        _: RunContext,
        messages: list[ModelMessage]) -> list[ModelMessage]:
    processed_messages = await keep_only_most_recent_by_pattern(
        _, messages, HistoryPattern(start="<folder_structure", end="</folder_structure>"))
    return processed_messages


async def keep_only_most_recent_entity_context(
        ctx: RunContext,
        messages: list[ModelMessage]) -> list[ModelMessage]:
    processed_messages = await keep_only_most_recent_by_pattern(
        ctx, messages, HistoryPattern(start="<entity_context", end="</entity_context>"))

    return processed_messages


# This is a subset of the keep_only_most_recent_project_description, in case we show the mount group outside of the project description
async def keep_only_most_recent_mount_node(
        _: RunContext,
        messages: list[ModelMessage]) -> list[ModelMessage]:
    processed_messages = await keep_only_most_recent_by_pattern(
        _, messages, HistoryPattern(start="<mount_node", end="</mount_node>"))
    return processed_messages


async def keep_only_most_recent_launched_runs_status(
        _: RunContext,
        messages: list[ModelMessage]) -> list[ModelMessage]:
    processed_messages = await keep_only_most_recent_by_pattern(
        _, messages, HistoryPattern(start="<launched_runs_status", end="</launched_runs_status>"))
    return processed_messages
