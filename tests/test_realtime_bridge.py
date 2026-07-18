import argparse
import unittest
from unittest.mock import patch

import veil_realtime_bridge as bridge


class RealtimeBridgeTest(unittest.TestCase):
    def _args(self):
        return argparse.Namespace(
            entity_id="codex-live",
            name="CodexLive",
            role="model",
            tier="full_participant",
            channel="general",
            constraint="",
            notes="test",
            task_ttl=300,
            poll_tasks=True,
            emit_empty_tasks=False,
        )

    def test_handshake_advertises_task_delegation(self):
        captured = {}

        def fake_post_json(url, payload, timeout=5.0):
            captured["url"] = url
            captured["payload"] = payload
            return payload

        with patch.object(bridge, "_post_json", side_effect=fake_post_json), patch.object(bridge, "_emit"):
            bridge.handshake("http://test", self._args())

        self.assertEqual(captured["url"], "http://test/api/participants/handshake")
        self.assertIn("task_delegation", captured["payload"]["capabilities"])

    def test_task_create_posts_to_task_api(self):
        captured = {}

        def fake_post_json(url, payload, timeout=5.0):
            captured["url"] = url
            captured["payload"] = payload
            return {"task_id": 1, "status": "pending"}

        command = {
            "type": "task_create",
            "target_entity": "claude-code-sonnet",
            "task_type": "query",
            "payload": {"prompt": "status?"},
        }
        with patch.object(bridge, "_post_json", side_effect=fake_post_json), patch.object(bridge, "_emit"):
            bridge.create_task("http://test", self._args(), command)

        self.assertEqual(captured["url"], "http://test/api/tasks")
        self.assertEqual(captured["payload"]["from_entity"], "codex-live")
        self.assertEqual(captured["payload"]["target_entity"], "claude-code-sonnet")
        self.assertEqual(captured["payload"]["payload"], {"prompt": "status?"})

    def test_task_complete_patches_to_task_api(self):
        captured = {}

        def fake_patch_json(url, payload, timeout=5.0):
            captured["url"] = url
            captured["payload"] = payload
            return {"task_id": 7, "status": "complete"}

        command = {"type": "task_complete", "task_id": 7, "result": "done"}
        with patch.object(bridge, "_patch_json", side_effect=fake_patch_json), patch.object(bridge, "_emit"):
            bridge.update_task("http://test", self._args(), command, "complete")

        self.assertEqual(captured["url"], "http://test/api/tasks/7")
        self.assertEqual(captured["payload"], {
            "entity_id": "codex-live",
            "action": "complete",
            "result": "done",
        })


if __name__ == "__main__":
    unittest.main()
