from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from zipfile import ZipFile


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from proposal_format.docx_builder import build_docx
from proposal_format.parser import parse_file
from proposal_format.verifier import all_passed, verify_docx


FIXTURES = Path(__file__).resolve().parent / "fixtures"
PROFILE = json.loads((SKILL_ROOT / "references" / "format-profile.json").read_text(encoding="utf-8"))


class GenerationTests(unittest.TestCase):
    def test_generated_docx_passes_machine_checks(self) -> None:
        model = parse_file(FIXTURES / "teacher-day.input.md")
        with tempfile.TemporaryDirectory(dir=SKILL_ROOT) as temp_dir:
            output = Path(temp_dir) / "teacher-day.docx"
            build_docx(model, PROFILE, output)
            checks = verify_docx(output, model, PROFILE)
            failures = [check.as_dict() for check in checks if not check.passed]
            self.assertTrue(all_passed(checks), failures)

    def test_contract_markers_do_not_enter_docx(self) -> None:
        model = parse_file(FIXTURES / "third-level.input.md")
        with tempfile.TemporaryDirectory(dir=SKILL_ROOT) as temp_dir:
            output = Path(temp_dir) / "third-level.docx"
            build_docx(model, PROFILE, output)
            with ZipFile(output) as archive:
                document_xml = archive.read("word/document.xml").decode("utf-8")
            for marker in ("【主标题开始】", "【主标题结束】", "【落款】", "## ", "### "):
                self.assertNotIn(marker, document_xml)

    def test_repeated_generation_has_stable_content_and_styles(self) -> None:
        model = parse_file(FIXTURES / "third-level.input.md")
        with tempfile.TemporaryDirectory(dir=SKILL_ROOT) as temp_dir:
            first = Path(temp_dir) / "first.docx"
            second = Path(temp_dir) / "second.docx"
            build_docx(model, PROFILE, first)
            build_docx(model, PROFILE, second)
            with ZipFile(first) as a, ZipFile(second) as b:
                for part in ("word/document.xml", "word/styles.xml", "word/footer1.xml", "word/sectPr.xml"):
                    if part in a.namelist() or part in b.namelist():
                        self.assertIn(part, a.namelist())
                        self.assertIn(part, b.namelist())
                        self.assertEqual(a.read(part), b.read(part), part)


if __name__ == "__main__":
    unittest.main()
