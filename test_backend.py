import unittest
import tempfile
import os
from backend import MuseBridge, PermissionDenied, InvalidState, MessageStatus

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.b = MuseBridge(); self.b.grant("alex", "message_content")

    def test_message_requires_consent_and_approval(self):
        with self.assertRaises(PermissionDenied): self.b.prepare_message("m0", "jordan", "alex", "secret")
        self.b.prepare_message("m1", "alex", "jordan", "Let's talk")
        with self.assertRaises(InvalidState): self.b.deliver_message("m1")
        self.b.approve_message("m1", "alex")
        self.assertEqual(self.b.deliver_message("m1").status, MessageStatus.DELIVERED)

    def test_revocation_blocks_future_delivery(self):
        self.b.prepare_message("m2", "alex", "jordan", "Draft")
        self.b.revoke("alex", "message_content")
        with self.assertRaises(PermissionDenied): self.b.approve_message("m2", "alex")

    def test_delivery_is_idempotent(self):
        self.b.prepare_message("m3", "alex", "jordan", "One time")
        self.b.approve_message("m3", "alex")
        first = self.b.deliver_message("m3"); second = self.b.deliver_message("m3")
        self.assertIs(first, second)
        self.assertEqual(len([x for x in self.b.audit if x["action"] == "message_delivered"]), 1)

    def test_agreement_needs_both_people(self):
        self.b.create_agreement("a1", "Confirm plans Thursday")
        self.b.approve_agreement("a1", "alex")
        self.assertEqual(self.b.agreements["a1"].status, "pending")
        self.assertEqual(self.b.approve_agreement("a1", "jordan").status, "approved")

    def test_state_survives_reload(self):
        fd, path = tempfile.mkstemp(); os.close(fd)
        try:
            first = MuseBridge(path)
            first.grant("alex", "message_content")
            first.prepare_message("persisted", "alex", "jordan", "saved")
            second = MuseBridge(path)
            self.assertIn("persisted", second.messages)
            self.assertIn("message_content", second.permissions["alex"])
            self.assertEqual(len(second.audit), 2)
        finally:
            os.unlink(path)

if __name__ == "__main__": unittest.main()
