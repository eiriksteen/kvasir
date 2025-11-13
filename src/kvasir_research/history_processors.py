import copy
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
                if isinstance(part, ToolReturnPart):
                    if "<begin_file>" in part.content:
                        file_path = part.content.split(
                            "file_path=")[1].split(">")[0]
                        if not file_path in last_idx_per_file_path:
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
                    if "<begin_file>" in part.content:
                        file_path = part.content.split(
                            "file_path=")[1].split(">")[0]
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


def get_last_notebook_message_index(messages: list[ModelMessage]) -> int:
    """
    Find the index of the last message containing a full analysis/notebook.
    Returns the index of the ToolReturnPart message containing the notebook.
    Returns -1 if no analysis is found.
    """
    for i in range(len(messages) - 1, -1, -1):
        message = messages[i]

        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, ToolReturnPart):
                    if "<notebook>" in part.content:
                        return i

    return -1


async def keep_only_most_recent_notebook(
        _: RunContext,
        messages: list[ModelMessage]) -> list[ModelMessage]:
    """
    Keep only the most recent analysis/notebook in the history.
    Older analysis returns are replaced with a simple success message.
    """
    last_analysis_idx = get_last_notebook_message_index(messages)

    if last_analysis_idx == -1:
        # No analysis found, return messages as is
        return messages

    updated_messages = []

    for i, message in enumerate(messages):
        message_to_add = message
        updated_message = copy.deepcopy(message)
        parts_modified = False

        if isinstance(message, ModelRequest):
            for idx, part in enumerate(message.parts):
                if isinstance(part, ToolReturnPart):
                    if "<notebook>" in part.content:
                        if i < last_analysis_idx:
                            # This is an older analysis, replace with simple message
                            updated_message.parts[idx].content = "Successfully updated the analysis notebook."
                            parts_modified = True

        if parts_modified:
            message_to_add = updated_message

        updated_messages.append(message_to_add)

    return updated_messages
