# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

"""Hand-written extras shim for the session API.

Preserved across regen via the Makefile ``rsync --exclude=*_shim.py`` rule.
Re-exports the typed session-stream classes from
``session_stream_shim`` so callers can write
``from arkruntime.types.session import ManagedAgentsAgentMessageEvent``.
"""

from __future__ import annotations

from .session_stream_shim import (
    ListSessionEventsResponse,
    ManagedAgentsAgentMCPToolResultEvent,
    ManagedAgentsAgentMCPToolUseEvent,
    ManagedAgentsAgentMessageEvent,
    ManagedAgentsAgentThinkingEvent,
    ManagedAgentsAgentThreadContextCompactedEvent,
    ManagedAgentsAgentThreadMessageReceivedEvent,
    ManagedAgentsAgentThreadMessageSentEvent,
    ManagedAgentsAgentToolResultEvent,
    ManagedAgentsAgentToolUseEvent,
    ManagedAgentsModelUsage,
    ManagedAgentsOutputContentBlock,
    ManagedAgentsRetryStatus,
    ManagedAgentsSessionErrorEvent,
    ManagedAgentsSessionErrorPayload,
    ManagedAgentsSessionStatusIdleEvent,
    ManagedAgentsSessionStatusRunningEvent,
    ManagedAgentsSessionStatusTerminatedEvent,
    ManagedAgentsSessionThreadCreatedEvent,
    ManagedAgentsSessionThreadStatusIdleEvent,
    ManagedAgentsSessionThreadStatusRunningEvent,
    ManagedAgentsSessionThreadStatusTerminatedEvent,
    ManagedAgentsSpanModelRequestEndEvent,
    ManagedAgentsSpanModelRequestStartEvent,
    ManagedAgentsSpanOutcomeEvaluationEndEvent,
    ManagedAgentsSpanOutcomeEvaluationOngoingEvent,
    ManagedAgentsSpanOutcomeEvaluationStartEvent,
    ManagedAgentsStopReason,
    ManagedAgentsUnknownSessionEvent,
    ManagedAgentsUserDefineOutcomeEvent,
    ManagedAgentsUserInterruptEvent,
    ManagedAgentsUserMessageEvent,
    ManagedAgentsUserToolConfirmationEvent,
    SessionStreamEvent,
    decode_session_event,
)

__all__ = [
    "ListSessionEventsResponse",
    "ManagedAgentsAgentMCPToolResultEvent",
    "ManagedAgentsAgentMCPToolUseEvent",
    "ManagedAgentsAgentMessageEvent",
    "ManagedAgentsAgentThinkingEvent",
    "ManagedAgentsAgentThreadContextCompactedEvent",
    "ManagedAgentsAgentThreadMessageReceivedEvent",
    "ManagedAgentsAgentThreadMessageSentEvent",
    "ManagedAgentsAgentToolResultEvent",
    "ManagedAgentsAgentToolUseEvent",
    "ManagedAgentsModelUsage",
    "ManagedAgentsOutputContentBlock",
    "ManagedAgentsRetryStatus",
    "ManagedAgentsSessionErrorEvent",
    "ManagedAgentsSessionErrorPayload",
    "ManagedAgentsSessionStatusIdleEvent",
    "ManagedAgentsSessionStatusRunningEvent",
    "ManagedAgentsSessionStatusTerminatedEvent",
    "ManagedAgentsSessionThreadCreatedEvent",
    "ManagedAgentsSessionThreadStatusIdleEvent",
    "ManagedAgentsSessionThreadStatusRunningEvent",
    "ManagedAgentsSessionThreadStatusTerminatedEvent",
    "ManagedAgentsSpanModelRequestEndEvent",
    "ManagedAgentsSpanModelRequestStartEvent",
    "ManagedAgentsSpanOutcomeEvaluationEndEvent",
    "ManagedAgentsSpanOutcomeEvaluationOngoingEvent",
    "ManagedAgentsSpanOutcomeEvaluationStartEvent",
    "ManagedAgentsStopReason",
    "ManagedAgentsUnknownSessionEvent",
    "ManagedAgentsUserDefineOutcomeEvent",
    "ManagedAgentsUserInterruptEvent",
    "ManagedAgentsUserMessageEvent",
    "ManagedAgentsUserToolConfirmationEvent",
    "SessionStreamEvent",
    "decode_session_event",
]
