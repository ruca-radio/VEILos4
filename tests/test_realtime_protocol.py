import os
import tempfile
import unittest

from src import veil_chat_protocol as protocol


class RealtimeProtocolTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.old_db = protocol.CHAT_DB
        protocol.CHAT_DB = os.path.join(self.tmpdir.name, "veil_chat.db")
        protocol.init_chat_db()

    def tearDown(self):
        protocol.CHAT_DB = self.old_db
        self.tmpdir.cleanup()

    def test_message_events_are_replayed_after_cursor(self):
        first_id = protocol.save_message("general", "human-patrick", "Patrick", "hello")
        second_id = protocol.save_message("general", "model-codex", "Codex", "reply")

        events = protocol.get_message_events(after_id=first_id)

        self.assertEqual([event["id"] for event in events], [second_id])
        self.assertEqual(events[0]["event_type"], "message")
        self.assertEqual(events[0]["channel"], "general")
        self.assertEqual(events[0]["sender_name"], "Codex")
        self.assertEqual(protocol.get_latest_message_id(), second_id)

    def test_message_events_filter_channels_and_exclude_sender(self):
        general_id = protocol.save_message("general", "human-patrick", "Patrick", "general")
        protocol.save_message("building", "model-codex", "Codex", "build")
        protocol.save_message("general", "model-codex", "Codex", "self")

        events = protocol.get_message_events(
            after_id=general_id - 1,
            channels=["general"],
            exclude_sender_id="model-codex",
        )

        self.assertEqual([event["id"] for event in events], [general_id])
        self.assertEqual(events[0]["content"], "general")


if __name__ == "__main__":
    unittest.main()
