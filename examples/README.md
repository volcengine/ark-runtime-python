# Examples

Runnable examples for the `arkruntime` Python SDK. Each file expects `ARK_API_KEY` in the environment:

```bash
export ARK_API_KEY=...
python examples/async_responses_create.py
```

| File | What it shows |
|---|---|
| `async_responses_create.py` | Async client + POST /v1/responses with streaming |
| `async_responses_doubao_app.py` | Responses with Doubao app tools |
| `async_responses_video.py` | Video input in responses |
| `multimodal_embeddings.py` | POST /embeddings/multimodal |
| `content_generation_tasks.py` | full lifecycle on POST /contents/generations/tasks (create / poll / list / delete) |
| `image_generations.py` | POST /images/generations — Seedream T2I, Seededit edit-from-image, sequential image generation |
| `agents.py` | Managed-Agents: Agent lifecycle — Create/Get/List/Update/ListVersions/Delete |
| `environments.py` | Managed-Agents: Environment lifecycle — Create/Get/List/Update/Delete (cloud + unrestricted networking) |
| `sessions_loop.py` | Managed-Agents: end-to-end agent loop — Agent + Env + Session, send user.message, stream events until idle |
| `memory_stores.py` | Managed-Agents: MemoryStore + nested Memory CRUD |

The Managed-Agents examples additionally accept `ARK_MODEL_ID` for the model id (falls back to a `${YOUR_MODEL_ID}` placeholder that will 400 at runtime).

Examples only cover currently-implemented APIs. See the `API Coverage` table in the top-level README for the roadmap.
