from __future__ import annotations

from pathlib import Path
import sys
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from proposal_format.parser import InputContractError, parse_file, parse_text


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class ParserTests(unittest.TestCase):
    def test_teacher_day_structure(self) -> None:
        model = parse_file(FIXTURES / "teacher-day.input.md")
        self.assertEqual(
            model.counts(),
            {
                "title_lines": 2,
                "heading1": 9,
                "heading2": 3,
                "heading3": 0,
                "paragraph": 15,
                "signature": 1,
            },
        )
        self.assertEqual(model.title_lines[0], "“师引前路，情满东大”")
        self.assertEqual(model.signature.organization, "东北大学学生会")
        self.assertEqual(model.signature.date, "2026年9月7日")

    def test_third_level_under_heading1_and_heading2(self) -> None:
        model = parse_file(FIXTURES / "third-level.input.md")
        level_three = [block.text for block in model.blocks if block.type == "heading3"]
        self.assertEqual(
            level_three,
            [
                "1.第一项工作于9月1日完成，负责人为甲。",
                "2.第二项工作于9月2日完成，负责人为乙。",
                "1.工作人员于10：30到场，完成物料清点。",
                "2.负责人于11:00检查场地，并记录结果。",
            ],
        )

    def test_visible_punctuation_is_preserved(self) -> None:
        model = parse_file(FIXTURES / "third-level.input.md")
        visible = "\n".join(block.text for block in model.blocks)
        self.assertIn("10：30", visible)
        self.assertIn("11:00", visible)
        self.assertIn("2026年", model.signature.date)

    def assert_contract_error(self, text: str, code: str) -> None:
        with self.assertRaises(InputContractError) as captured:
            parse_text(text)
        self.assertIn(code, {issue.code for issue in captured.exception.issues})

    def test_missing_title_marker_stops(self) -> None:
        self.assert_contract_error(
            "主标题\n【主标题结束】\n\n## 一、正文\n\n内容。\n\n【落款】\n单位\n2026年1月1日",
            "E_TITLE_POSITION",
        )

    def test_heading_level_jump_stops(self) -> None:
        self.assert_contract_error(
            "【主标题开始】\n主标题\n【主标题结束】\n\n### （一）二级标题\n\n【落款】\n单位\n2026年1月1日",
            "E_LEVEL_JUMP",
        )

    def test_duplicate_signature_stops(self) -> None:
        self.assert_contract_error(
            "【主标题开始】\n主标题\n【主标题结束】\n\n## 一、正文\n\n内容。\n\n【落款】\n单位\n日期\n【落款】",
            "E_SIGNATURE_COUNT",
        )

    def test_signature_must_be_last(self) -> None:
        self.assert_contract_error(
            "【主标题开始】\n主标题\n【主标题结束】\n\n## 一、正文\n\n内容。\n\n【落款】\n单位\n日期\n多余内容",
            "E_SIGNATURE_SHAPE",
        )

    def test_unsupported_markdown_stops(self) -> None:
        cases = {
            "E_TABLE": "| 项目 | 金额 |",
            "E_IMAGE": "![图片](image.png)",
            "E_ATTACHMENT": "## 二、附件",
            "E_UNKNOWN_HEADING": "# 错误标题",
            "E_LIST": "- 项目符号",
        }
        for code, bad_line in cases.items():
            with self.subTest(code=code):
                text = (
                    "【主标题开始】\n主标题\n【主标题结束】\n\n"
                    "## 一、正文\n\n内容。\n\n"
                    f"{bad_line}\n\n【落款】\n单位\n2026年1月1日"
                )
                self.assert_contract_error(text, code)

    def test_wrapped_paragraph_stops(self) -> None:
        self.assert_contract_error(
            "【主标题开始】\n主标题\n【主标题结束】\n\n## 一、正文\n\n第一行\n第二行\n\n【落款】\n单位\n2026年1月1日",
            "E_WRAPPED_LINE",
        )


if __name__ == "__main__":
    unittest.main()
