import asyncio
from pydantic import ValidationError
from astera.chatbot.chatbot_agent import chatbot_agent


async def test_chatbot_interactive():

    print("\n=== Chatbot Interactive Test ===")
    print("Type your messages and press Enter. The conversation will end when the chatbot state is 'done'.")
    print("To exit manually, press Ctrl+C\n")

    try:
        while True:
            # Get user input
            user_message = input("\nYou: ")

            async with chatbot_agent.run_stream(user_message) as result:
                async for message, last in result.stream_structured(debounce_by=0.1):
                    try:
                        chatbot_output = await result.validate_structured_result(
                            message, allow_partial=not last
                        )

                        print(chatbot_output)
                    except ValidationError as exc:
                        if all(
                            e['type'] == 'missing' and e['loc'] == (
                                'response',)
                            for e in exc.errors()
                        ):
                            continue
                        else:
                            raise

    except KeyboardInterrupt:
        print("\nTest terminated by user")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_chatbot_interactive())
