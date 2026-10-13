from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from proposal_format.environment import EnvironmentResult, find_missing_fonts
from proposal_format.parser import parse_file
from proposal_format.report import create_report, finalize_report
from proposal_format.verifier import CheckResult
import format_proposal


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class ValidationTests(unittest.TestCase):
    def test_all_required_fonts_are_reported_when_none_are_installed(self) -> None:
        required = [
            {"name": "方正小标宋_GBK", "aliases": ["方正小标宋"]},
            {"name": "方正黑体_GBK", "aliases": ["方正黑体"]},
            {"name": "方正楷体_GBK", "aliases": ["方正楷体"]},
            {"name": "方正仿宋_GBK", "aliases": ["方正仿宋"]},
            {"name": "Times New Roman", "aliases": []},
        ]
        self.assertEqual(
            find_missing_fonts(required, installed=set()),
            [font["name"] for font in required],
        )

    def test_generic_font_token_does_not_satisfy_required_font(self) -> None:
        required = [{"name": "方正仿宋_GBK", "aliases": ["FZFangSong-Z02"]}]
        self.assertEqual(find_missing_fonts(required, installed={"fangsong"}), ["方正仿宋_GBK"])

    def test_failed_environment_creates_no_formal_output(self) -> None:
        for error in ("缺少规定字体：方正仿宋_GBK。", "未找到 Microsoft Word。"):
            with self.subTest(error=error), tempfile.TemporaryDirectory(dir=SKILL_ROOT) as temp_dir:
                output_dir = Path(temp_dir) / "formal-output"
                environment = EnvironmentResult(ok=False, errors=[error], details={})
                args = argparse.Namespace(
                    input=str(FIXTURES / "third-level.input.md"),
                    output_dir=str(output_dir),
                )
                with patch.object(format_proposal, "check_environment", return_value=environment):
                    with redirect_stdout(io.StringIO()):
                        exit_code = format_proposal.command_build(args)
                self.assertEqual(exit_code, 3)
                self.assertFalse(output_dir.exists())

    def test_report_requires_all_pages_before_pass(self) -> None:
        model = parse_file(FIXTURES / "third-level.input.md")
        environment = EnvironmentResult(ok=True, details={"missing_fonts": []})
        with tempfile.TemporaryDirectory(dir=SKILL_ROOT) as temp_dir:
            temp = Path(temp_dir)
            report = temp / "report.md"
            output = temp / "output.docx"
            output.touch()
            create_report(
                report,
                FIXTURES / "third-level.input.md",
                output,
                model,
                environment,
                [CheckResult("example", True, "通过", "通过")],
                expected_pages=2,
                word_version="16.0",
            )
            with self.assertRaisesRegex(ValueError, "必须检查全部 2 页"):
                finalize_report(report, "pass", 1)

            finalize_report(report, "pass", 2, "两页均已检查。")
            text = report.read_text(encoding="utf-8")
            self.assertIn("<!-- overall-status:start -->通过<!-- overall-status:end -->", text)
            self.assertIn("- 已检查页数：2", text)
            self.assertIn("两页均已检查。", text)

    def test_failed_visual_review_is_recorded(self) -> None:
        model = parse_file(FIXTURES / "third-level.input.md")
        environment = EnvironmentResult(ok=True, details={})
        with tempfile.TemporaryDirectory(dir=SKILL_ROOT) as temp_dir:
            temp = Path(temp_dir)
            report = temp / "report.md"
            output = temp / "output.docx"
            output.touch()
            create_report(report, FIXTURES / "third-level.input.md", output, model, environment, [], 1, "16.0")
            finalize_report(report, "fail", 1, "第1页出现异常换行。")
            text = report.read_text(encoding="utf-8")
            self.assertIn("<!-- overall-status:start -->失败<!-- overall-status:end -->", text)
            self.assertIn("第1页出现异常换行。", text)


if __name__ == "__main__":
    unittest.main()
