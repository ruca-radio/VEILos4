import os
import tempfile
import unittest

from fastapi.testclient import TestClient

from src import veil_chat_protocol as protocol
import veil_chat


class RealtimeApiTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.old_db = protocol.CHAT_DB
        protocol.CHAT_DB = os.path.join(self.tmpdir.name, "veil_chat.db")
        protocol.init_chat_db()
        self.client = TestClient(veil_chat.app)

    def tearDown(self):
        protocol.CHAT_DB = self.old_db
        self.tmpdir.cleanup()

    def test_events_endpoint_returns_cursor_and_events(self):
        first_id = protocol.save_message("general", "human-patrick", "Patrick", "first")
        second_id = protocol.save_message("general", "model-codex", "Codex", "second")

        response = self.client.get(f"/api/events?after_id={first_id}&channels=general")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["cursor"], second_id)
        self.assertEqual(body["latest_cursor"], second_id)
        self.assertEqual([event["id"] for event in body["events"]], [second_id])
        self.assertEqual(body["events"][0]["channel"], "general")


if __name__ == "__main__":
    unittest.main()
