# Examples

Runnable examples for the `arkruntime` Python SDK. Set `ARK_API_KEY` and, for most examples, `ARK_MODEL` to a model ID available in your account.

```bash
export ARK_API_KEY=...
export ARK_MODEL=...
python examples/volc/responses/async_create.py
```

All service-calling examples are grouped by cloud:

- [`volc/`](./volc) uses `Ark.volc()` / `AsyncArk.volc()` and Volcengine China model IDs.
- [`byteplus/`](./byteplus) uses `Ark.byteplus()` / `AsyncArk.byteplus()` and BytePlus model IDs.

[`self_hosted_worker.py`](./self_hosted_worker.py) demonstrates the Managed-Agents self-hosted worker poll/handle loop and uses the client's production default `https://ark.cn-beijing.volces.com/api/v3`.

[`self_hosted_mcp_worker/`](./self_hosted_mcp_worker) demonstrates how to discover tools from a local stdio MCP server, convert them into Agent custom tool declarations, and execute them through the self-hosted worker.

The paired multimodal and sparse embedding examples default to `doubao-embedding-vision-251215` / `skylark-embedding-vision-251215`. The paired image examples default to `doubao-seedream-5-0-pro-260628` / `dola-seedream-5-0-pro-260628`. The paired video-generation examples default to `doubao-seedance-2-0-fast-260128` / `dreamina-seedance-2-0-fast-260128`.

MCP is available in both clouds and its examples explicitly send `ark-beta-mcp: true`. Other built-in tools are CN-only: Web Search sends `ark-beta-web-search: true`, and Doubao App sends `ark-beta-doubao-app: true`.
