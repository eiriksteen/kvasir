import copy
from pydantic_ai import RunContext, Agent
from pydantic_ai.messages import ModelMessage, ModelResponse, ModelRequest, ToolCallPart, ToolReturnPart, SystemPromptPart, RetryPromptPart
from synesis_api.agents.model_integration.deps import ModelIntegrationDeps
from synesis_api.utils import get_model


def get_last_script_message_index(messages: list[ModelMessage]) -> int:
    """
    Find the index of the last message containing a script modification tool call.
    Returns the index of the ToolCallPart message, not the ToolReturnPart.
    Returns -1 if no script modification is found.
    """
    script_tools = [
        "write_script",
        "replace_script_lines",
        "add_script_lines",
        "delete_script_lines"
    ]

    for i in range(len(messages) - 1, -1, -1):
        message = messages[i]
        if isinstance(message, ModelResponse):
            for part in message.parts:
                if isinstance(part, ToolCallPart) and part.tool_name in script_tools:
                    return i

    return -1


async def keep_only_most_recent_script(
    ctx: RunContext[ModelIntegrationDeps],
        messages: list[ModelMessage]) -> list[ModelMessage]:
    """
    Keep only the most recent script in the history.
    """
    last_script_index = get_last_script_message_index(messages)

    if last_script_index == -1:
        # No script modifications found, return messages as is
        return messages

    updated_messages = []

    for i, message in enumerate(messages[::-1]):
        original_index = len(messages) - 1 - i
        message_to_add = message
        updated_message = copy.deepcopy(message)
        parts_modified = False

        # if isinstance(message, ModelResponse):
        #     for idx, part in enumerate(message.parts):
        #         if isinstance(part, ToolCallPart):
        #             args_dict = json.loads(part.args) if isinstance(
        #                 part.args, str) else part.args
        #             k = "script" if "script" in args_dict else "new_code" if "new_code" in args_dict else None

        #             if k:
        #                 # Always omit tool call scripts since they've already been executed
        #                 args_dict[k] = "[OLD CODE OMITTED]"
        #                 part.args = json.dumps(args_dict)
        #                 updated_message.parts[idx] = part
        #                 parts_modified = True

        if isinstance(message, ModelRequest):
            for idx, part in enumerate(message.parts):
                if isinstance(part, ToolReturnPart):
                    if "<begin_script>" in part.content and original_index < last_script_index:
                        # This is an older script, omit it
                        part.content = "Successfully updated the script. The script is not automatically run and validated, you must call the result submission tool to submit the script for validation and feedback."
                        updated_message.parts[idx] = part
                        parts_modified = True

        if parts_modified:
            message_to_add = updated_message

        updated_messages.append(message_to_add)

    updated_messages = updated_messages[::-1]

    print("="*20, "KEEP ONLY MOST RECENT SCRIPT", "="*20)
    for i, message in enumerate(updated_messages):
        print("-"*20)
        print(f"Message {i+1}: {message}")
        print("-"*20)
    print("="*50)

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
    ctx: RunContext[ModelIntegrationDeps],
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

    # system prompt, summary, and the messages from cutoff onwards
    output_messages = [messages[0]] + \
        summary_run.new_messages() + messages[cutoff_index:]

    print("--------------------------------")
    print(
        f"MESSAGE HISTORY SUMMARIZER APPLIED, WENT FROM SIZE {len(messages)} TO {len(output_messages)}")
    print(
        f"Last script modification at index: {last_script_index}, cutoff at: {cutoff_index}")
    print("--------------------------------")

    # print("="*20, "PRE-SUMMARY MESSAGES", "="*20)
    # for i, message in enumerate(messages):
    #     print("-"*20)
    #     print(f"Message {i+1}: {message}")
    #     print("-"*20)
    # print("="*50)

    print("="*20, "SUMMARIZER OUTPUT", "="*20)
    for i, message in enumerate(output_messages):
        print("-"*20)
        print(f"Message {i+1}: {message}")
        print("-"*20)
    print("="*50)

    return output_messages
