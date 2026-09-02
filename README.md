# Ark Runtime Python SDK

The official Python library for accessing ModelArk on Volcengine and BytePlus. It provides synchronous and asynchronous clients, typed models, streaming, authentication, retries, and timeout configuration.

## Installation

```bash
pip install arkruntime
```

## Choose Volcengine or BytePlus

Set `ARK_API_KEY`, then choose the client factory for the service you use. The factory configures the correct base URL and region; request construction and all subsequent SDK calls are the same.

### Volcengine (China)

```python
from arkruntime import Ark

client = Ark.volc()
# or explicitly: Ark.volc(api_key="your-api-key")
```

### BytePlus (BP)

```python
from arkruntime import Ark

client = Ark.byteplus()
# or explicitly: Ark.byteplus(api_key="your-api-key")
```

Use a model ID available in the corresponding Volcengine or BytePlus account. Model IDs can differ between the two services; the examples use `doubao-seed-2-1-pro-260628` for Volcengine and `seed-2-0-lite-260428` for BytePlus. Override either default with `ARK_MODEL`.

The async client provides the same factories: `AsyncArk.volc()` and `AsyncArk.byteplus()`.

## Quick start

### Responses API

```python
import os
from arkruntime import Ark

client = Ark.volc()

response = client.responses.create(
    model=os.environ.get("ARK_MODEL", "doubao-seed-2-1-pro-260628"),
    input="Explain how large language models work in three sentences.",
)
for item in response.output or []:
    if item.type == "message":
        for content in item.content:
            if content.type == "output_text":
                print(content.text)
```

For BytePlus, change only the client line to `client = Ark.byteplus()` and set `ARK_MODEL` to a BytePlus model ID.

## Usage

### Chat Completions

```python
import os
from arkruntime import Ark

client = Ark.volc()

completion = client.chat.completions.create(
    model=os.environ.get("ARK_MODEL", "doubao-seed-2-1-pro-260628"),
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Write a haiku about programming."},
    ],
)
print(completion.choices[0].message.content)
```

## Streaming

Both the Responses and Chat Completions APIs support streaming via `stream=True`.

### Streaming responses

```python
import os
from arkruntime import Ark

client = Ark.volc()

stream = client.responses.create(
    model=os.environ.get("ARK_MODEL", "doubao-seed-2-1-pro-260628"),
    input="Count from 1 to 10 slowly.",
    stream=True,
)
for event in stream:
    print(event)
```

### Streaming chat completions

```python
import os
from arkruntime import Ark

client = Ark.volc()

stream = client.chat.completions.create(
    model=os.environ.get("ARK_MODEL", "doubao-seed-2-1-pro-260628"),
    messages=[{"role": "user", "content": "Count from 1 to 10 slowly."}],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

## Async usage

Every synchronous method has an async counterpart on `AsyncArk`.

```python
import asyncio
import os
from arkruntime import AsyncArk

client = AsyncArk.volc()

async def main():
    response = await client.responses.create(
        model=os.environ.get("ARK_MODEL", "doubao-seed-2-1-pro-260628"),
        input="Explain quantum computing briefly.",
    )
    for item in response.output or []:
        if item.type == "message":
            for content in item.content:
                if content.type == "output_text":
                    print(content.text)

asyncio.run(main())
```

## Vision

Pass images alongside text using multimodal content blocks.

```python
import os
from arkruntime import Ark

client = Ark.volc()

completion = client.chat.completions.create(
    model=os.environ.get("ARK_MODEL", "doubao-seed-2-1-pro-260628"),
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What is in this image?"},
                {"type": "image_url", "image_url": {"url": "https://example.com/photo.jpg"}},
            ],
        }
    ],
)
print(completion.choices[0].message.content)
```

## Function calling

```python
import json
import os
from arkruntime import Ark

client = Ark.volc()

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"},
                },
                "required": ["location"],
            },
        },
    }
]

completion = client.chat.completions.create(
    model=os.environ.get("ARK_MODEL", "doubao-seed-2-1-pro-260628"),
    messages=[{"role": "user", "content": "What is the weather in Beijing?"}],
    tools=tools,
)

tool_call = completion.choices[0].message.tool_calls[0]
print(f"Function: {tool_call.function.name}")
print(f"Arguments: {tool_call.function.arguments}")
```

## File uploads

```python
from arkruntime import Ark

client = Ark.volc()

# Upload a file
file = client.files.create(file=open("data.jsonl", "rb"), purpose="batch")
print(file.id)

# List files
for f in client.files.list():
    print(f.id, f.filename)

# Delete a file
client.files.delete(file.id)
```

## Error handling

The SDK raises typed exceptions for API errors.

```python
from arkruntime import Ark
from arkruntime._exceptions import ArkAPIError, ArkRateLimitError, ArkAuthenticationError

client = Ark.volc()

try:
    client.chat.completions.create(
        model="doubao-seed-2-1-pro-260628",
        messages=[{"role": "user", "content": "Hello"}],
    )
except ArkRateLimitError:
    print("Rate limited — back off and retry.")
except ArkAuthenticationError:
    print("Invalid API key.")
except ArkAPIError as e:
    print(f"API error {e.status_code}: {e}")
```

The exception hierarchy:

```
ArkError
 +-- ArkAPIError
      +-- ArkAPIStatusError
      |    +-- ArkBadRequestError          (400)
      |    +-- ArkAuthenticationError       (401)
      |    +-- ArkPermissionDeniedError     (403)
      |    +-- ArkNotFoundError             (404)
      |    +-- ArkConflictError             (409)
      |    +-- ArkUnprocessableEntityError  (422)
      |    +-- ArkRateLimitError            (429)
      |    +-- ArkInternalServerError       (500)
      +-- ArkAPIConnectionError
      |    +-- ArkAPITimeoutError
      +-- ArkAPIResponseValidationError
```

## Retries and timeouts

The client automatically retries failed requests (default: 2 retries) with backoff for transient errors.

```python
from arkruntime import Ark

# Customize retries and timeout
client = Ark.volc(
    max_retries=5,
    timeout=120.0,  # seconds
)
```

Per-request overrides are also supported:

```python
client.chat.completions.create(
    model="doubao-seed-2-1-pro-260628",
    messages=[{"role": "user", "content": "Hello"}],
    timeout=30.0,
)
```

## Batch inference

`client.batch.*` provides a synchronous high-throughput path with per-model concurrency control and automatic retry on `408`/`409`/`429`/`5xx`. See the [batch examples](./examples/batch) for thread-pool and async fan-out patterns.

```python
from arkruntime import Ark

client = Ark.volc(timeout=24 * 3600)

result = client.batch.chat.completions.create(
    model="doubao-seed-2-1-pro-260628",
    messages=[{"role": "user", "content": "Hello"}],
)
print(result)
```

## Examples

For detailed usage guidance and legacy migration, see
[`docs/README.md`](docs/README.md) and
[`docs/migration.md`](docs/migration.md).

See the [examples/](./examples) directory for runnable scripts:

- `volc/` -- Volcengine China examples for Chat, Responses, images, video generation, embeddings, files, tokenization, batch APIs, and resource APIs
- `byteplus/` -- supported BytePlus counterparts using the BytePlus client and regional model IDs

MCP examples are provided for both clouds and explicitly send `ark-beta-mcp: true`. Other built-in-tool examples are CN-only and show their required beta headers.

## Requirements

- Python >= 3.8
- httpx >= 0.23.0
- pydantic >= 2.0
- typing-extensions >= 4.7

## License

This project is licensed under the Apache License 2.0. See [LICENSE](./LICENSE).
For third-party open-source software notices, see
[THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md).
