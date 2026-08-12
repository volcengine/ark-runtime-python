"""Function calling example for chat.completions.

Mirrors the Go SDK's chat/function_call example: registers a single
get_current_weather tool, then sends the same request both
non-streaming and streaming, aggregating tool-call deltas in the
streaming branch by their index.
"""

import os

from arkruntime import Ark

# Authentication
# 1.If you authorize your endpoint using an API key, you can set your api key to environment variable "ARK_API_KEY"
client = Ark()
MODEL = os.environ.get("ENDPOINT_ID", "doubao-seed-2-1-pro-260628")

WEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_current_weather",
        "description": "Get the current weather in a given location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                },
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
            "required": ["location"],
        },
    },
}

if __name__ == "__main__":
    messages = [{"role": "user", "content": "What's the weather like in Boston today?"}]

    # Non-streaming:
    print("----- function call request -----")
    completion = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=[WEATHER_TOOL],
    )
    print(completion.model_dump_json(indent=2))

    # Streaming:
    print("----- function call stream request -----")
    stream = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=[WEATHER_TOOL],
        stream=True,
    )
    final_calls: dict[int, dict] = {}
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta.content:
            print(delta.content, end="")
        for tc in delta.tool_calls or []:
            cur = final_calls.setdefault(tc.index, {"id": "", "name": "", "args": ""})
            if tc.id and not cur["id"]:
                cur["id"] = tc.id
            if tc.function:
                if tc.function.name and not cur["name"]:
                    cur["name"] = tc.function.name
                if tc.function.arguments:
                    cur["args"] += tc.function.arguments
    print()
    for idx, call in sorted(final_calls.items()):
        print(f"tool_call[{idx}] id={call['id']} name={call['name']} args={call['args']}")
