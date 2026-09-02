# Migrate from the legacy Python SDK

This guide covers the runtime clients imported from:

- `volcenginesdkarkruntime`
- `byteplussdkarkruntime`

Both migrate to the `arkruntime` distribution and Python package.

## 1. Migration order

Migrate one API flow at a time:

1. Choose the target cloud: Volcengine (CN) or BytePlus.
2. Install `arkruntime`, update imports, and select the regional sync or async
   client factory.
3. Verify every request dictionary's discriminator, nesting, and field names.
4. Update non-streaming Responses output traversal and streaming event types.
5. Preserve response IDs, call IDs, and approval IDs across multi-turn flows.
6. Add the required beta header to every built-in-tool request and remove any
   CN-only tool from a BytePlus target.
7. Compile and smoke-test that flow before migrating the next one.

Do not apply a project-wide regular-expression replacement to request bodies or
stream handlers. Their correct mapping depends on runtime structure and intent.

## 2. Dependency, import, and client mapping

Install the new package:

```bash
pip install arkruntime
```

| Legacy | New |
|---|---|
| `from volcenginesdkarkruntime import Ark` | `from arkruntime import Ark` |
| `from byteplussdkarkruntime import Ark` | `from arkruntime import Ark` |
| legacy `.types...` import root | `arkruntime.types...` |
| `Ark(...)` | CN: `Ark.volc(...)`; BP: `Ark.byteplus(...)` |
| `AsyncArk(...)` | CN: `AsyncArk.volc(...)`; BP: `AsyncArk.byteplus(...)` |

Remove `volcengine-python-sdk` or `byteplus-python-sdk-v2` from application
dependencies only after verifying no other imports need that distribution.
`arkruntime` itself may install a Volcengine dependency for its authentication
implementation; that is not a reason to keep legacy runtime imports.

If legacy code sets `base_url`, inspect it manually. Prefer the regional factory
default. Retain a custom URL only when the deployment explicitly requires one.

## 3. Request-body mapping

Most keyword-based calls remain recognizable, but migration must validate the
body as a discriminated union rather than assuming every old dictionary is
accepted.

| Intent | New body |
|---|---|
| simple Responses prompt | `input="..."` |
| message input | `input=[{"role": "user", "content": ...}]` |
| text content part | `{"type": "input_text", "text": "..."}` |
| image content part | `{"type": "input_image", "image_url": "..."}` |
| function result | `{"type": "function_call_output", "call_id": id, "output": value}` |
| MCP approval | `{"type": "mcp_approval_response", "approval_request_id": id, "approve": True}` |

Preserve `previous_response_id` when continuing a stored response. Preserve the
same tool declarations in the follow-up request when required by the flow.
Never collapse a content-part list into a string if it also contains media.

If an application creates request dictionaries dynamically, add fixture tests
for the final kwargs passed to `responses.create` or `chat.completions.create`.

## 4. Output and stream mapping

Non-streaming Responses output must be traversed:

```python
for item in response.output or []:
    if item.type == "message":
        for content in item.content:
            if content.type == "output_text":
                print(content.text)
```

There is no `response.output_text` convenience property in this SDK.

Chat stream text remains on `chunk.choices[0].delta.content`. Responses streams
are typed unions. Import event types from `arkruntime.types.responses` and use
`isinstance`:

```python
if isinstance(event, ResponseTextDeltaEvent):
    consume(event.delta)
elif isinstance(event, ResponseCompletedEvent):
    response_id = event.response.id
```

Common legacy type mappings are:

| Legacy | New public type |
|---|---|
| `ResponseFunctionToolCall` | `ItemFunctionToolCall` |
| `McpApprovalRequest` | `ItemFunctionMcpApprovalRequest` |
| deep per-file event imports | imports from `arkruntime.types.responses` |

For a function call, capture `call_id` from a
`ResponseOutputItemDoneEvent` whose item is `ItemFunctionToolCall`. For MCP,
capture the approval request item and the completed response ID. Async code uses
`await` plus `async for`; do not mechanically change it to the sync iteration
pattern.

## 5. Extra headers and regional behavior

Headers are per-call keyword arguments:

```python
client.responses.create(
    ...,
    extra_headers={"ark-beta-mcp": "true"},
)
```

MCP (`ark-beta-mcp`) works in CN and BytePlus. Web search
(`ark-beta-web-search`), knowledge search (`ark-beta-knowledge-search`), Doubao
App (`ark-beta-doubao-app`), and image process (`ark-beta-image-process`) are
CN-only. Remove these tools from a BytePlus migration rather than silently
dropping their headers or changing their request bodies.

## 6. Regional model IDs

Model names and endpoint IDs are cloud-specific. Prefer application
configuration, and update any legacy hard-coded default when changing clouds:

| API | Volcengine (CN) example | BytePlus example |
|---|---|---|
| Responses / Chat | `doubao-seed-2-1-pro-260628` | `seed-2-0-lite-260428` |
| Multimodal / sparse embeddings | `doubao-embedding-vision-251215` | `skylark-embedding-vision-251215` |
| Image generation | `doubao-seedream-5-0-pro-260628` | `dola-seedream-5-0-pro-260628` |
| Video generation | `doubao-seedance-2-0-fast-260128` | `dreamina-seedance-2-0-fast-260128` |

Use a model or endpoint ID provisioned for the target account if it differs
from these example defaults.

## 7. Validate the migration

1. Search for legacy runtime imports and direct `Ark(...)` / `AsyncArk(...)`
   construction; none should remain in migrated Ark Runtime code.
2. Run the project's formatter, type checker, and tests.
3. Run `python -m compileall` over migrated source.
4. Run one non-streaming request and verify output traversal.
5. Run sync or async streaming through a completed event and verify error paths.
6. Smoke-test each built-in tool with its beta header.
7. Validate CN and BytePlus separately when supporting both. Do not reuse a
   key, model, endpoint ID, or client between regions.

Compilation alone does not prove a migration is correct: dictionary bodies,
event dispatch, output traversal, regional model names, and headers are runtime
contracts.
