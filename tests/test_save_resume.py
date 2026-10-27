"""Synthetic receipt protocol; never a real image-save or host test."""
import unittest
import workflow_session as w


class SaveResumeTests(unittest.TestCase):
    def setUp(self):
        from verify_delivery_automation import AutomationTests
        self.fixture = AutomationTests(methodName='runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.accept()

    def test_receipt_arriving_before_ack_can_resume_same_intent_without_another_save(self):
        f = self.fixture
        w.save_intent(f.j, f.receipt)
        before = f.j.read_bytes()
        f.save_fixture(f.receipt, f.o, 'SYNTHETIC_SAVED_ONCE')
        receipt = f.receipt.read_bytes()
        try:
            w.save_intent(f.j, f.receipt)
        except FileExistsError as error:
            self.fail('A matching pending save must resume after its receipt arrives: '+str(error))
        self.assertEqual(f.j.read_bytes(), before)
        self.assertEqual(f.receipt.read_bytes(), receipt)
        self.assertNotIn('save_completed', w._load(f.j)['milestones'])
        w.complete_save(f.j, f.receipt)
        acknowledged = f.j.read_bytes()
        w.save_intent(f.j, f.receipt)
        w.complete_save(f.j, f.receipt)
        self.assertEqual(f.j.read_bytes(), acknowledged)

    def test_unrelated_existing_receipt_still_cannot_start_an_intent(self):
        f = self.fixture
        f.save_fixture(f.receipt, f.o, 'SYNTHETIC_OLD_RECEIPT')
        before = f.j.read_bytes()
        with self.assertRaises(FileExistsError):
            w.save_intent(f.j, f.receipt)
        self.assertEqual(f.j.read_bytes(), before)
