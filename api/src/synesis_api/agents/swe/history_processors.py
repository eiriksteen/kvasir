import copy
from pydantic_ai import RunContext, Agent
from pydantic_ai.messages import ModelMessage, ModelResponse, ModelRequest, ToolCallPart, ToolReturnPart, SystemPromptPart, RetryPromptPart

from synesis_api.agents.swe.deps import SWEAgentDeps
from synesis_api.utils.pydanticai_utils import get_model


def get_last_script_message_index(messages: list[ModelMessage]) -> dict[str, int]:
    """
    Find the index of the last message containing a script modification tool call.
    Returns the index of the ToolCallPart message, not the ToolReturnPart.
    Returns -1 if no script modification is found.
    """
    # script_tools = [
    #     "write_script",
    #     "replace_script_lines",
    #     "add_script_lines",
    #     "delete_script_lines"
    # ]

    last_idx_per_script = {}

    for i in range(len(messages) - 1, -1, -1):
        message = messages[i]

        # if isinstance(message, ModelResponse):
        #     for part in message.parts:
        #         if isinstance(part, ToolCallPart) and part.tool_name in script_tools:
        #             return i
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


summarizer_agent = Agent(
    get_model(),
    instructions=(
        "Summarize the contents of this entire message history. "
        "Focus on the flow of messages and tool calls, and what has happened in sequential order. "
        "All important information must be included."
        "You may get a previous summary from the user, and in this case update the summary to include the new information."
        "Omit unnecessary formulations such as 'This summary now covers every step'"
        "Keep it concise, focus on what has happened in the message history."
        "Do not include any information about the system prompt in the summary, as it will be kept in the message history."
        f"Start by 'The message history after the system prompt and before the last few messages has been summarized for conciseness. Here is the summary:'"
    ),
    output_type=str
)


async def summarize_message_history(
    ctx: RunContext[SWEAgentDeps],
        messages: list[ModelMessage],
        keep_pastk: int = 10
) -> list[ModelMessage]:

    tools_to_summarize = [
        "write_script",
        "replace_script_lines",
        "add_script_lines",
        "delete_script_lines"
    ]

    if len(messages) <= keep_pastk + 2:
        return messages

    assert len(messages[0].parts) == 1 and isinstance(
        messages[0].parts[0], SystemPromptPart)

    last_script_index = get_last_script_message_index(messages)

    if last_script_index != -1:
        cutoff_index = max(last_script_index, len(messages) - keep_pastk)
    else:
        cutoff_index = len(messages) - keep_pastk

    messages_to_summarize = [messages[0]] + [
        m for m in messages[ctx.deps.history_cutoff_index:cutoff_index] if any([(isinstance(p, ToolCallPart)
                                                                                 or isinstance(p, ToolReturnPart)
                                                                                 or isinstance(p, RetryPromptPart)
                                                                                 )
                                                                                and p.tool_name in tools_to_summarize
                                                                                for p in m.parts])
    ]

    summary_run = await summarizer_agent.run(
        f"The previous summary is: {ctx.deps.history_summary}", message_history=messages_to_summarize)

    ctx.deps.history_summary = summary_run.output
    ctx.deps.history_cutoff_index = cutoff_index

    output_messages = [messages[0]] + \
        summary_run.new_messages() + messages[cutoff_index:]

    return output_messages
