# Ark Runtime Python SDK documentation

This directory contains detailed usage and migration guidance for the Ark
Runtime Python SDK.

## Choose the right document

- [Usage guide](usage.md): installation, regional clients,
  request bodies, sync/async streaming, output parsing, and built-in tools.
- [Migration guide](migration.md): migrate from the legacy Volcengine or
  BytePlus Python SDK.
- [`../examples/volc`](../examples/volc): runnable Volcengine examples.
- [`../examples/byteplus`](../examples/byteplus): runnable BytePlus examples.

## Important usage rules

1. Create clients with `Ark.volc()` / `AsyncArk.volc()` for CN or
   `Ark.byteplus()` / `AsyncArk.byteplus()` for BytePlus. Do not supply a CN URL
   to a BytePlus client or the reverse.
2. Keep credentials in `ARK_API_KEY`; never place a key in code, prompts,
   generated patches, tests, logs, or notebooks.
3. Preserve the documented request body shape and type discriminators. A dict
   union member needs the correct `type`, field names, and nesting.
4. Streaming APIs return events or chunks, not the final response object.
   Handle only the event types needed and safely ignore other valid events.
5. A non-streaming Responses object has no `response.output_text` convenience
   field. Traverse `response.output`, message content, and `output_text` items.
6. MCP works in CN and BytePlus. Other hosted built-in tools shown here are
   CN-only and require their matching `ark-beta-*` header.

## Minimal verification

```bash
python -m compileall src examples
python -m pytest
```

Also run one non-streaming and one streaming call in the intended cloud. Test
each built-in tool independently so missing access or headers cannot be hidden
by a successful ordinary request.
