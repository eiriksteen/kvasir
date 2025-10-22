import copy
from pydantic_ai import RunContext
from pydantic_ai.messages import ModelMessage, ModelRequest, ToolReturnPart

from project_server.agents.swe.deps import SWEAgentDeps


def get_last_script_message_index(messages: list[ModelMessage]) -> dict[str, int]:
    """
    Find the index of the last message containing a script modification tool call.
    Returns the index of the ToolCallPart message, not the ToolReturnPart.
    Returns -1 if no script modification is found.
    """

    last_idx_per_script = {}

    for i in range(len(messages) - 1, -1, -1):
        message = messages[i]

        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, ToolReturnPart):
                    if "<begin_script>" in part.content:
                        script_name = part.content.split(
                            "file_name=")[1].split(">")[0]
                        if not script_name in last_idx_per_script:
                            last_idx_per_script[script_name] = i

    return last_idx_per_script


async def keep_only_most_recent_script(
        _: RunContext[SWEAgentDeps],
        messages: list[ModelMessage]) -> list[ModelMessage]:
    """
    Keep only the most recent script in the history.
    """
    last_idx_per_script = get_last_script_message_index(messages)

    if not last_idx_per_script:
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
                    if "<begin_script>" in part.content:
                        script_name = part.content.split(
                            "file_name=")[1].split(">")[0]
                        if original_index < last_idx_per_script[script_name]:
                            # This is an older script, omit it
                            part.content = "Successfully updated the script. The script is not automatically run and validated, you must call the result submission tool to submit the script for validation and feedback."
                            updated_message.parts[idx] = part
                            parts_modified = True

        if parts_modified:
            message_to_add = updated_message

        updated_messages.append(message_to_add)

    updated_messages = updated_messages[::-1]

    return updated_messages
