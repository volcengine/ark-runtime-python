"""End-to-end agent-loop example — Create Agent + Environment + Session,
send a text prompt, stream events until the loop settles, print the
assistant's response.

Exercises the smallest useful call sequence:

    POST   /api/v3/agents                       (client.agents.create)
    POST   /api/v3/environments                 (client.environments.create)
    POST   /api/v3/sessions                     (client.sessions.create)
    POST   /api/v3/sessions/:id/events          (client.sessions.events.send)
    GET    /api/v3/sessions/:id/events (stream) (client.sessions.events.stream)

Uses typed pydantic classes end-to-end on both send and receive so callers
get IDE completion + pyright/mypy field-name checks. Mirrors the Go SDK's
examples/sessions_loop/main.go 1:1.

    export ARK_API_KEY=...
    export ARK_MODEL_ID=doubao-seed-2-1-pro-260628
    python examples/sessions_loop.py
"""

from __future__ import annotations

import os
import threading
import time

from arkruntime import Ark
from arkruntime.types.agent import ModelConfig, ToolItem
from arkruntime.types.environment import EnvConfig, NetworkingConfig
from arkruntime.types.session import (
    ManagedAgentsAgentMessageEvent,
    ManagedAgentsSessionErrorEvent,
    ManagedAgentsSessionStatusIdleEvent,
    ManagedAgentsSessionStatusTerminatedEvent,
    ManagedAgentsTextBlock,
    ManagedAgentsUserMessageEventParams,
)

STOP_EVENT_TYPES = (
    ManagedAgentsSessionStatusIdleEvent,
    ManagedAgentsSessionStatusTerminatedEvent,
    ManagedAgentsSessionErrorEvent,
)


def main() -> None:
    api_key = os.environ.get("ARK_API_KEY")
    if not api_key:
        raise SystemExit("set ARK_API_KEY")
    model_id = os.environ.get("ARK_MODEL_ID", "${YOUR_MODEL_ID}")

    client = Ark(api_key=api_key)

    ag = client.agents.create(
        name=f"example-loop-agent-{time.time_ns()}",
        model=ModelConfig(id=model_id),
        system="You are a helpful assistant. Answer the user's question briefly.",
        tools=[ToolItem(type="agent_toolset_20260401")],
    )
    print(f"agent:      id={ag.id}")

    env = client.environments.create(
        name=f"example-loop-env-{time.time_ns()}",
        config=EnvConfig(
            type="cloud",
            networking=NetworkingConfig(type="unrestricted"),
        ),
    )
    print(f"env:        id={env.id}")

    sess = client.sessions.create(
        agent=ag.id,
        environment_id=env.id,
        title="ark-runtime-python example loop",
    )
    print(f"session:    id={sess.id}\n")

    try:
        # Open the SSE stream first, then send the user message asynchronously
        # so we don't race and miss the earliest events.
        def _send() -> None:
            time.sleep(0.5)  # Warmup so SSE is fully attached before we push.
            client.sessions.events.send(
                sess.id,
                events=[
                    ManagedAgentsUserMessageEventParams(
                        type="user.message",
                        content=[
                            ManagedAgentsTextBlock(
                                type="text",
                                text="What's the tallest mountain? One sentence.",
                            )
                        ],
                    )
                ],
            )

        threading.Thread(target=_send, daemon=True).start()

        assistant_out: list[str] = []
        for event in client.sessions.events.stream(sess.id):
            ev = event.data
            if ev is None:
                continue
            print(f"[EVT] {event.type}")

            if isinstance(ev, ManagedAgentsAgentMessageEvent):
                for block in ev.content:
                    if block.text:
                        assistant_out.append(block.text)
            elif isinstance(ev, STOP_EVENT_TYPES):
                break

        joined = "".join(assistant_out).strip()
        if joined:
            print(f"\nassistant → {joined}")
        else:
            print("\n(no assistant text captured — check the [EVT] trace above)")
    finally:
        # Cleanup — delete session → env → agent.
        for delete, obj_id in (
            (client.sessions.delete, sess.id),
            (client.environments.delete, env.id),
            (client.agents.delete, ag.id),
        ):
            try:
                delete(obj_id)
            except Exception as exc:  # noqa: BLE001
                print(f"cleanup {delete.__qualname__}({obj_id}): {exc}")


if __name__ == "__main__":
    main()
