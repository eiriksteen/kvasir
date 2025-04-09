import asyncio
from pydantic import ValidationError
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.settings import ModelSettings
from pydantic_ai.providers.openai import OpenAIProvider
from synesis_api.secrets import OPENAI_API_KEY, OPENAI_API_MODEL


provider = OpenAIProvider(api_key=OPENAI_API_KEY)

model = OpenAIModel(
    model_name=OPENAI_API_MODEL,
    provider=provider
)


chatbot_agent = Agent(
    model,
    system_prompt="You are gathering project requirements for an AI/ML project from a user.",
    model_settings=ModelSettings(temperature=0.1)
)


async def test_chatbot_interactive():

    print("\n=== Chatbot Interactive Test ===")
    print("Type your messages and press Enter. The conversation will end when the chatbot state is 'done'.")
    print("To exit manually, press Ctrl+C\n")

    message_history = []
    try:
        while True:
            # Get user input
            user_message = input("\nYou: ")

            async with chatbot_agent.run_stream(user_message, message_history=message_history) as result:
                async for text in result.stream(debounce_by=0.01):
                    print(text)
                print(result.new_messages())
                print("@"*10)
                print(result.new_messages_json())
                message_history += result.new_messages()

    except KeyboardInterrupt:
        print("\nTest terminated by user")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_chatbot_interactive())
