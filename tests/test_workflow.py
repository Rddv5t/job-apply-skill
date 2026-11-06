"""Run with: python -m unittest discover -s tests -v"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "tracker", ROOT / "skills" / "job-apply" / "scripts" / "tracker.py")
tracker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tracker)


class WorkflowTests(unittest.TestCase):
    def test_configured_role_and_industry_exclusions(self):
        config = {"role_priority": ["产品经理"],
                  "excluded_role_keywords": ["市场", "营销", "GTM", "软件产品经理"],
                  "excluded_industry_keywords": ["电子烟"]}
        cases = [
            ({"position": "GTM产品经理"}, "skip_role"),
            ({"position": "产品市场实习生"}, "skip_role"),
            ({"position": "软件产品经理"}, "skip_role"),
            ({"position": "硬件产品经理", "industry": "电子烟"}, "skip_industry"),
            ({"position": "硬件产品经理", "industry": "机器人",
              "description": "参与市场调研，与营销团队协作"}, "eligible"),
        ]
        for extra, expected in cases:
            with self.subTest(extra=extra):
                candidate = {"company": "示例新公司", "location": "城市甲", **extra}
                self.assertEqual(tracker.screen(config, [candidate], [])[0]["decision"], expected)
        candidate = {"company": "示例新公司", "position": "软件产品经理", "location": "城市甲"}
        self.assertEqual(tracker.screen({}, [candidate], [])[0]["decision"], "eligible")

    def test_company_alias_and_unknown_previous_role(self):
        config = {"company_aliases": {"Example EN": "示例甲"}, "duplicate_scope": "company"}
        history = [{"company": "示例甲", "status": "已投递", "position": ""}]
        candidates = [{"company": "Example EN", "position": "产品经理", "location": "城市甲"}]
        self.assertEqual(tracker.screen(config, candidates, history)[0]["decision"], "skip_duplicate")
        config["duplicate_scope"] = "company-role"
        self.assertEqual(tracker.screen(config, candidates, history)[0]["decision"], "review_duplicate")

    def test_city_and_overseas_boundaries(self):
        config = {"allowed_locations": ["城市甲"], "allow_overseas": True,
                  "excluded_regions": ["东南亚"]}
        cases = [
            ({"location": "城市乙"}, "skip_location"),
            ({"location": "Singapore", "country": "Singapore", "overseas": True}, "skip_location"),
            ({"location": "伦敦", "country": "英国", "overseas": True}, "review_location"),
            ({"location": "伦敦", "country": "英国", "region": "欧洲", "overseas": True}, "eligible"),
            ({"location": "城市甲、城市乙"}, "review_location"),
        ]
        for extra, decision in cases:
            with self.subTest(extra=extra):
                candidate = {"company": "示例新公司", "position": "产品经理", **extra}
                self.assertEqual(tracker.screen(config, [candidate], [])[0]["decision"], decision)

    def test_records_evidence_merge_and_safe_export(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "records.json"
            record = {"company": "=HYPERLINK(example)", "position": "<script>alert(1)</script>",
                      "date": "", "status": "已投递", "evidence": "用户明确确认，具体日期未知"}
            tracker.upsert(path, record)
            tracker.upsert(path, {**record, "status": "面试", "evidence": "用户提供面试通知"})
            rows = tracker.read_json(path)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["date"], "")
            self.assertEqual(rows[0]["status"], "面试")
            tracker.export_records(rows, Path(temp) / "report")
            page = (Path(temp) / "report/application-tracker.html").read_text(encoding="utf-8")
            self.assertIn("&lt;script&gt;alert", page)
            csv = (Path(temp) / "report/application-records.csv").read_text(encoding="utf-8-sig")
            self.assertIn("'=HYPERLINK", csv)
            with self.assertRaises(ValueError):
                tracker.upsert(path, {**record, "evidence": ""})

    def test_installer_preview_idempotence_and_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "skills"
            command = [sys.executable, str(ROOT / "install.py"), "--target", str(target)]
            env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
            def run(extra, success=True):
                result = subprocess.run(command + extra, capture_output=True, env=env)
                self.assertEqual(result.returncode == 0, success, result.stderr.decode(errors="replace"))
                return result
            run(["--dry-run"])
            self.assertFalse(target.exists())
            run([])
            cache = target / "job-apply/scripts/__pycache__"
            cache.mkdir()
            (cache / "tracker.pyc").write_bytes(b"runtime cache")
            run([])
            skill = target / "job-apply/SKILL.md"
            skill.write_text("local changes", encoding="utf-8")
            run([], success=False)
            run(["--overwrite"])
            backups = list(target.glob("job-apply.backup-*/SKILL.md"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding="utf-8"), "local changes")


if __name__ == "__main__":
    unittest.main()
