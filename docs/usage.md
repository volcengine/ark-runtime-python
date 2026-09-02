# Usage guide

Use this guide when creating or modifying a Python application with Ark
Runtime. Copy complete shapes from the matching regional example, then make the
smallest application-specific change.

## 1. Install and configure

```bash
pip install arkruntime
export ARK_API_KEY="..."
```

Keep the key outside source control. Read the model or endpoint ID from
application configuration, such as `ARK_MODEL`, rather than hard-coding it in a
reusable package.

## 2. Select the cloud and sync mode

Only client creation changes; API calls and request setup remain the same.

```python
from arkruntime import Ark, AsyncArk

# Volcengine (CN)
client = Ark.volc()
async_client = AsyncArk.volc()

# BytePlus
client = Ark.byteplus()
async_client = AsyncArk.byteplus()
```

The factories read `ARK_API_KEY` by default and also accept `api_key=...` when
the application already manages secrets securely.

Current regional example defaults are:

| API | Volcengine (CN) | BytePlus |
|---|---|---|
| Responses / Chat | `doubao-seed-2-1-pro-260628` | `seed-2-0-lite-260428` |
| Multimodal / sparse embeddings | `doubao-embedding-vision-251215` | `skylark-embedding-vision-251215` |
| Image generation | `doubao-seedream-5-0-pro-260628` | `dola-seedream-5-0-pro-260628` |
| Video generation | `doubao-seedance-2-0-fast-260128` | `dreamina-seedance-2-0-fast-260128` |

Use the model or endpoint ID provisioned for the user's account if it differs.

BytePlus currently has no model for the text-only `/embeddings` endpoint, so
its examples use `/embeddings/multimodal` instead.

## 3. Build request bodies

Simple Responses request:

```python
response = client.responses.create(
    model=model,
    input="Explain LLMs in one sentence.",
)
```

Structured input uses discriminated dictionaries:

```python
response = client.responses.create(
    model=model,
    input=[
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": "Describe this image"},
                {"type": "input_image", "image_url": image_url},
            ],
        }
    ],
)
```

When editing a body, preserve:

- discriminator values such as `input_text`, `function_call_output`, and
  `mcp_approval_response`;
- exact snake_case field names;
- list versus scalar forms of `input` and `content`;
- `previous_response_id`, call IDs, and approval IDs across turns;
- user-provided extra fields, timeouts, and headers.

Typed request dictionaries from `arkruntime.types` can be useful to type
check a reusable library. Ordinary application code can use the documented
dict forms directly.

## 4. Read non-streaming output

The Responses object does not provide `response.output_text`. Traverse its
output items:

```python
for item in response.output or []:
    if item.type != "message":
        continue
    for content in item.content:
        if content.type == "output_text":
            print(content.text)
```

Do not assume the first output item is a message: reasoning and tool-call items
may precede it.

## 5. Handle streams

Chat streams yield chunks:

```python
stream = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "Hello"}],
    stream=True,
)
for chunk in stream:
    if not chunk.choices:
        continue
    text = chunk.choices[0].delta.content
    if text:
        print(text, end="")
```

Responses streams yield typed events:

```python
from arkruntime.types.responses import (
    ResponseCompletedEvent,
    ResponseTextDeltaEvent,
)

stream = client.responses.create(model=model, input="Hello", stream=True)
for event in stream:
    if isinstance(event, ResponseTextDeltaEvent):
        print(event.delta, end="")
    elif isinstance(event, ResponseCompletedEvent):
        response_id = event.response.id
```

For async clients, await creation where the example does and use
`async for event in stream`. Function calling and MCP require capturing typed
output-item events as well as the completed response ID. Do not treat every
event as a text event or fail on a valid event the application does not use.

## 6. Built-in tools and headers

Pass `extra_headers` on every call that contains a beta tool:

```python
response = client.responses.create(
    model=model,
    input="Summarize the repository",
    tools=[{"type": "mcp", "server_label": "docs", "server_url": url}],
    extra_headers={"ark-beta-mcp": "true"},
)
```

| Tool | Cloud | Required header |
|---|---|---|
| MCP | CN and BytePlus | `ark-beta-mcp: true` |
| Web search | CN only | `ark-beta-web-search: true` |
| Knowledge search | CN only | `ark-beta-knowledge-search: true` |
| Doubao App | CN only | `ark-beta-doubao-app: true` |
| Image process | CN only | `ark-beta-image-process: true` |

Do not add a CN-only tool to BytePlus code. Application-defined function calls
are not hosted built-in tools.

## 7. Navigate the examples

Use [`examples/volc`](../examples/volc) or
[`examples/byteplus`](../examples/byteplus). Both trees include Chat and
Responses streaming/non-streaming usage and their region's other supported
APIs. The CN tree includes the CN-only built-in-tool examples.

Use this routing table instead of reshaping a Chat example for another API:

| Intent | Example path below the region directory |
|---|---|
| Chat stream/non-stream, reasoning, vision, tools | `chat/` |
| Responses stream/non-stream and hosted tools | `responses/` |
| Text embeddings (Volcengine only) | `cn/embeddings.py` |
| Sparse or multimodal embeddings | `sparse_embeddings.py`, `multimodal_embeddings.py` |
| Image generation | `image_generations.py` |
| Video generation | `content_generation_tasks.py` |
| Files | `files/` |
| Batch APIs | `batch/` |
| Agents, sessions, memory stores, environments | matching top-level script |
| Token counting | `tokenization.py` |

Sync and async examples are named explicitly. Do not convert between them
unless the application's execution model requires it.

## 8. Completion checklist

- Imports come from `arkruntime`, not a legacy package.
- Sync/async and CN/BytePlus client choices are explicit.
- No credentials are present in source or output.
- Dict discriminators, nesting, IDs, custom fields, and headers are preserved.
- Non-streaming Responses text is read from output items.
- Streaming code handles the correct chunk/event types.
- Built-in tools include their headers and respect regional support.
- Compile and test commands pass.
