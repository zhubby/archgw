from src.commons.globals import handler_map
from src.core.function_calling import ArchFunctionHandler, Message


test_input_history = [
    {"role": "user", "content": "how is the weather in chicago for next 5 days?"},
    {
        "role": "assistant",
        "model": "Arch-Function",
        "content": '```json\n{"tool_calls": [{"name": "get_current_weather", "arguments": {"days": 5, "location": "Chicago, Illinois"}}]}\n```',
    },
    {
        "role": "tool",
        "model": "Arch-Function",
        "content": '{"location":"Chicago%2C%20Illinois","temperature":[{"date":"2025-04-14","temperature":{"min":53,"max":65},"units":"Farenheit","query_time":"2025-04-14 17:01:52.432817+00:00"},{"date":"2025-04-15","temperature":{"min":85,"max":97},"units":"Farenheit","query_time":"2025-04-14 17:01:52.432830+00:00"},{"date":"2025-04-16","temperature":{"min":62,"max":78},"units":"Farenheit","query_time":"2025-04-14 17:01:52.432835+00:00"},{"date":"2025-04-17","temperature":{"min":89,"max":101},"units":"Farenheit","query_time":"2025-04-14 17:01:52.432839+00:00"},{"date":"2025-04-18","temperature":{"min":86,"max":104},"units":"Farenheit","query_time":"2025-04-14 17:01:52.432843+00:00"}],"units":"Farenheit"}',
    },
    {
        "role": "assistant",
        "model": "gpt-4o-2024-08-06",
        "content": '{"response": "Based on the forecast data you provided, here is the weather for the next 5 days in Chicago:\\n\\n- **April 14, 2025**: The temperature will range between 53\\u00b0F and 65\\u00b0F. \\n- **April 15, 2025**: The temperature will range between 85\\u00b0F and 97\\u00b0F.\\n- **April 16, 2025**: The temperature will range between 62\\u00b0F and 78\\u00b0F.\\n- **April 17, 2025**: The temperature will range between 89\\u00b0F and 101\\u00b0F.\\n- **April 18, 2025**: The temperature will range between 86\\u00b0F and 104\\u00b0F.\\n\\nPlease note that the temperatures are given in Fahrenheit."}',
    },
    {"role": "user", "content": "what about seattle?"},
]


def test_update_fc_history():
    message_history = []

    for h in test_input_history:
        message_history.append(Message(**h))

    handler: ArchFunctionHandler = handler_map["Arch-Function"]
    updated_history = handler._process_messages(message_history)
    assert len(updated_history) == 5
    # ensure that tool role does not exist anymore
    assert all([h["role"] != "tool" for h in updated_history])
