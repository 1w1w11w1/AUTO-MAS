from __future__ import annotations

import asyncio
import unittest
from typing import Any, cast

from app.plugins import EventBus, PluginEventNames


class EventBusTestCase(unittest.TestCase):
    def test_emit_uses_normalized_event_name(self) -> None:
        event_bus = EventBus()
        received: list[dict[str, str]] = []

        event_bus.on(f" {PluginEventNames.TASK_START} ", received.append)

        asyncio.run(event_bus.emit(PluginEventNames.TASK_START, {"task_id": "task-1"}))

        self.assertEqual(received, [{"task_id": "task-1"}])

    def test_off_normalizes_event_name(self) -> None:
        event_bus = EventBus()
        received: list[dict[str, str]] = []

        def record(payload: dict[str, str]) -> None:
            received.append(payload)

        event_bus.on(PluginEventNames.TASK_START, record)
        event_bus.off(f" {PluginEventNames.TASK_START} ", record)

        asyncio.run(event_bus.emit(PluginEventNames.TASK_START, {"task_id": "task-1"}))

        self.assertEqual(received, [])
        self.assertEqual(event_bus.handler_count, {})

    def test_emit_rejects_invalid_scope_before_dispatch(self) -> None:
        event_bus = EventBus()
        received: list[dict[str, str]] = []

        event_bus.on(PluginEventNames.TASK_START, received.append)

        with self.assertRaises(ValueError):
            asyncio.run(
                event_bus.emit(
                    PluginEventNames.TASK_START,
                    {"task_id": "task-1"},
                    scope=cast(Any, "invalid"),
                )
            )

        self.assertEqual(received, [])

    def test_emit_rejects_invalid_error_policy_before_dispatch(self) -> None:
        event_bus = EventBus()
        received: list[dict[str, str]] = []

        event_bus.on(PluginEventNames.TASK_START, received.append)

        with self.assertRaises(ValueError):
            asyncio.run(
                event_bus.emit(
                    PluginEventNames.TASK_START,
                    {"task_id": "task-1"},
                    error_policy=cast(Any, "stop"),
                )
            )

        self.assertEqual(received, [])


if __name__ == "__main__":
    unittest.main()
