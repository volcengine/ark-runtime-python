# Ark Runtime Python SDK

The official Python library for the Volcengine Ark runtime API. It provides convenient access to the Ark REST API from any Python 3.8+ application, with both synchronous and asynchronous clients.

## Installation

```bash
pip install arkruntime
```

## Usage

Create a client by setting the `ARK_API_KEY` environment variable:

```python
from arkruntime import Ark

client = Ark()
# or explicitly: Ark(api_key="your-api-key")
```

### Responses API

```python
import os
from arkruntime import Ark

client = Ark()

response = client.responses.create(
    model=os.environ.get("ARK_MODEL", "doubao-seed-2-1-pro-260628"),
    input="Explain how large language models work in three sentences.",
)
print(response.output_text)
```

### Chat Completions

```python
import os
from arkruntime import Ark

client = Ark()

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

client = Ark()

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

client = Ark()

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

client = AsyncArk()

async def main():
    response = await client.responses.create(
        model=os.environ.get("ARK_MODEL", "doubao-seed-2-1-pro-260628"),
        input="Explain quantum computing briefly.",
    )
    print(response.output_text)

asyncio.run(main())
```

## Vision

Pass images alongside text using multimodal content blocks.

```python
import os
from arkruntime import Ark

client = Ark()

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

client = Ark()

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

client = Ark()

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

client = Ark()

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
client = Ark(
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

client = Ark(timeout=24 * 3600)

result = client.batch.chat.completions.create(
    model="doubao-seed-2-1-pro-260628",
    messages=[{"role": "user", "content": "Hello"}],
)
print(result)
```

## API coverage

| API | Client path |
|---|---|
| Responses | `client.responses.create()` |
| Chat Completions | `client.chat.completions.create()` |
| Embeddings | `client.embeddings.create()` |
| Multimodal Embeddings | `client.multimodal_embeddings.create()` |
| Content Generation | `client.content_generation.tasks.create()` |
| Images | `client.images.generate()` |
| Files | `client.files.create()` / `.list()` / `.delete()` |
| Tokenization | `client.tokenization.create()` |
| Batch | `client.batch.chat.completions.create()` etc. |

## Examples

See the [examples/](./examples) directory for runnable scripts:

- `responses/` -- Responses API: multi-turn chat, function calling, structured output, video streaming
- `chat/` -- Chat Completions: basic, function calling, reasoning, structured output, vision
- `batch/` -- Batch inference: chat completions, embeddings, multimodal embeddings (sync + async)
- `files/` -- Files API: upload, wait for processing, list, delete
- `embeddings.py` -- Text embeddings
- `multimodal_embeddings.py` -- Multimodal embeddings with image input
- `content_generation_tasks.py` -- Video generation task lifecycle
- `image_generations.py` -- Image generation
- `tokenization.py` -- Tokenization API

## Development

This repo uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
uv sync                       # create venv + install runtime + dev deps
uv run pytest                 # run tests
uv run ruff check src/        # lint
uv run ruff format src/       # format
```

A pre-commit hook runs the same linting as CI:

```bash
uv run pre-commit install     # one-time setup
```

## Requirements

- Python >= 3.8
- httpx >= 0.23.0
- pydantic >= 2.0
- typing-extensions >= 4.7
