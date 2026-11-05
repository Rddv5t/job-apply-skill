import hashlib
import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/job-apply/scripts"
sys.path.insert(0, str(SCRIPTS))
import autumn_bridge
import prepare_autumn_tracker


class AutumnIntegrationTests(unittest.TestCase):
    def test_roundtrip_preserves_uncertain_state_blank_date_and_evidence(self):
        rows = [{"company": "示例公司", "position": "产品经理", "status": "待确认",
                 "date": "", "evidence": "提交超时，尚未复核", "source": "站内操作"}]
        backup = autumn_bridge.export_backup(rows)
        self.assertEqual(backup["records"][0]["stage"], "待投递")
        restored = autumn_bridge.import_backup(backup)[0]
        self.assertEqual(restored["status"], "待确认")
        self.assertEqual(restored["date"], "")
        self.assertEqual(restored["evidence"], rows[0]["evidence"])
        self.assertNotIn("resume", backup)

    def test_import_retains_unknown_dates_and_funnel_states(self):
        result = autumn_bridge.import_backup({"records": [
            {"company": "示例公司", "position": "示例岗位", "stage": "二面"},
            {"company": "示例另一公司", "stage": "未知状态"},
        ]})
        self.assertEqual(result[0]["status"], "面试")
        self.assertEqual(result[0]["date"], "")
        self.assertEqual(result[1]["status"], "待确认")
        with self.assertRaises(ValueError):
            autumn_bridge.import_backup({"records": [{"position": "missing company"}]})

    def test_upstream_source_integrity_and_changed_markers_fail_closed(self):
        data = b"example"
        digest = hashlib.sha1(b"blob 7\0" + data).hexdigest()
        prepare_autumn_tracker.verify_blob(data, {"path": "example.js", "sha": digest})
        with self.assertRaises(ValueError):
            prepare_autumn_tracker.verify_blob(b"modified", {"path": "example.js", "sha": digest})
        with self.assertRaises(ValueError):
            prepare_autumn_tracker.replace_once("unrelated source", "expected", "replacement")


if __name__ == "__main__":
    unittest.main()
