from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable


TITLE_START = "【主标题开始】"
TITLE_END = "【主标题结束】"
SIGNATURE_MARK = "【落款】"

CHINESE_DIGITS = {
    "零": 0,
    "〇": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}

H1_RE = re.compile(r"^## ([零〇一二两三四五六七八九十百]+)、\S.*$")
H2_RE = re.compile(r"^### （([零〇一二两三四五六七八九十百]+)）\S.*$")
H3_RE = re.compile(r"^(\d+)\.\S.*$")
UNKNOWN_MARK_RE = re.compile(r"^【.+】$")
ATTACHMENT_HEADING_RE = re.compile(
    r"^#{2,3}\s+(?:(?:[零〇一二两三四五六七八九十百]+、)|(?:（[零〇一二两三四五六七八九十百]+）))?附件"
)


@dataclass(frozen=True)
class ContractIssue:
    line: int
    code: str
    message: str
    text: str = ""
    suggestion: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "line": self.line,
            "code": self.code,
            "message": self.message,
            "text": self.text,
            "suggestion": self.suggestion,
        }


class InputContractError(ValueError):
    def __init__(self, issues: Iterable[ContractIssue], source: str = "<text>") -> None:
        self.issues = list(issues)
        self.source = source
        summary = "; ".join(
            f"{source}:{issue.line} [{issue.code}] {issue.message}" for issue in self.issues
        )
        super().__init__(summary)


@dataclass(frozen=True)
class Block:
    type: str
    text: str
    line: int


@dataclass(frozen=True)
class Signature:
    organization: str
    date: str
    line: int


@dataclass(frozen=True)
class ProposalDocument:
    title_lines: tuple[str, ...]
    blocks: tuple[Block, ...]
    signature: Signature
    source: str = "<text>"

    def expected_paragraphs(self) -> list[str]:
        return ["\n".join(self.title_lines), *[block.text for block in self.blocks], self.signature.organization, self.signature.date]

    def counts(self) -> dict[str, int]:
        result = {"title_lines": len(self.title_lines), "heading1": 0, "heading2": 0, "heading3": 0, "paragraph": 0, "signature": 1}
        for block in self.blocks:
            result[block.type] += 1
        return result


def chinese_number(value: str) -> int | None:
    if value == "十":
        return 10
    if "百" in value:
        left, _, right = value.partition("百")
        hundreds = CHINESE_DIGITS.get(left or "一")
        if hundreds is None:
            return None
        rest = chinese_number(right) if right else 0
        return None if rest is None else hundreds * 100 + rest
    if "十" in value:
        left, _, right = value.partition("十")
        tens = CHINESE_DIGITS.get(left or "一")
        ones = CHINESE_DIGITS.get(right, 0) if right else 0
        return None if tens is None or ones is None else tens * 10 + ones
    if len(value) == 1:
        return CHINESE_DIGITS.get(value)
    if value and all(char in CHINESE_DIGITS for char in value):
        digits = "".join(str(CHINESE_DIGITS[char]) for char in value)
        return int(digits)
    return None


def _issue(line: int, code: str, message: str, text: str = "", suggestion: str = "") -> ContractIssue:
    return ContractIssue(line=line, code=code, message=message, text=text, suggestion=suggestion)


def _nonempty_indices(lines: list[str]) -> list[int]:
    return [index for index, line in enumerate(lines) if line != ""]


def _groups(lines: list[str], start: int, end: int) -> list[tuple[int, list[str]]]:
    groups: list[tuple[int, list[str]]] = []
    current: list[str] = []
    current_line = 0
    for index in range(start, end):
        line = lines[index]
        if line == "":
            if current:
                groups.append((current_line, current))
                current = []
            continue
        if not current:
            current_line = index + 1
        current.append(line)
    if current:
        groups.append((current_line, current))
    return groups


def _unsupported_issue(line_number: int, raw: str) -> ContractIssue | None:
    if raw.startswith("```"):
        return _issue(line_number, "E_CODE_FENCE", "不支持代码围栏。", raw, "删除代码围栏，只保留策划案正文。")
    if re.search(r"!\[[^\]]*\]\([^)]*\)", raw) or "<img" in raw.lower():
        return _issue(line_number, "E_IMAGE", "首版不处理图片。", raw, "从待处理稿中移除图片。")
    if raw.startswith("|") and raw.endswith("|"):
        return _issue(line_number, "E_TABLE", "首版不处理 Markdown 表格。", raw, "从待处理稿中移除表格及其章节。")
    if re.match(r"^\s*[-*+]\s+", raw):
        return _issue(line_number, "E_LIST", "首版不处理项目符号列表。", raw, "将内容改写为普通正文或约定的三级内容段落。")
    if raw == "【附件】" or ATTACHMENT_HEADING_RE.match(raw):
        return _issue(line_number, "E_ATTACHMENT", "首版不处理附件正文。", raw, "从待处理稿中移除附件正文。")
    return None


def parse_text(text: str, source: str = "<text>") -> ProposalDocument:
    text = text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    lines = text.splitlines()
    issues: list[ContractIssue] = []

    for index, line in enumerate(lines, start=1):
        if line and line != line.strip():
            issues.append(_issue(index, "E_WHITESPACE", "非空行包含首尾空格。", line, "删除该行首尾空格。"))
        if line and "\t" in line:
            issues.append(_issue(index, "E_TAB", "不允许使用制表符控制版面。", line, "删除制表符，由格式程序设置缩进。"))

    nonempty = _nonempty_indices(lines)
    if not nonempty:
        raise InputContractError([_issue(1, "E_EMPTY", "输入文件为空。")], source)

    if lines[nonempty[0]] != TITLE_START:
        issues.append(_issue(nonempty[0] + 1, "E_TITLE_POSITION", "文件必须以主标题开始标记开头。", lines[nonempty[0]], f"将 `{TITLE_START}` 放在文件第一行。"))

    for marker, code in ((TITLE_START, "E_TITLE_START_COUNT"), (TITLE_END, "E_TITLE_END_COUNT"), (SIGNATURE_MARK, "E_SIGNATURE_COUNT")):
        positions = [i for i, line in enumerate(lines) if line == marker]
        if len(positions) != 1:
            issues.append(_issue((positions[0] + 1) if positions else 1, code, f"标记 `{marker}` 必须且只能出现一次。", suggestion="补齐或删除重复标记。"))

    if issues:
        raise InputContractError(issues, source)

    title_start = lines.index(TITLE_START)
    title_end = lines.index(TITLE_END)
    signature_index = lines.index(SIGNATURE_MARK)
    if not title_start < title_end < signature_index:
        raise InputContractError([_issue(1, "E_MARKER_ORDER", "主标题和落款标记顺序错误。", suggestion="按主标题开始、主标题结束、正文、落款的顺序排列。")], source)

    title_lines = lines[title_start + 1 : title_end]
    if not title_lines or any(not line for line in title_lines):
        issues.append(_issue(title_start + 1, "E_TITLE_CONTENT", "主标题标记内部必须包含连续的非空标题行。", suggestion="删除标题内部空行并补齐标题文字。"))
    for offset, title_line in enumerate(title_lines, start=title_start + 2):
        if title_line.startswith("#") or UNKNOWN_MARK_RE.match(title_line):
            issues.append(_issue(offset, "E_TITLE_LINE", "主标题内部只能包含可见标题文字。", title_line, "移除结构符号。"))

    tail = lines[signature_index + 1 :]
    if len(tail) != 2 or any(not line for line in tail):
        issues.append(_issue(signature_index + 1, "E_SIGNATURE_SHAPE", "落款标记后必须恰好包含单位和日期两行。", suggestion="删除多余内容，并补齐单位和日期。"))

    blocks: list[Block] = []
    seen_h1 = False
    expected_h1 = 1
    expected_h2 = 1
    expected_h3 = 1

    for line_number, group in _groups(lines, title_end + 1, signature_index):
        if len(group) != 1:
            issues.append(_issue(line_number, "E_WRAPPED_LINE", "一个自然段被人工拆成多行。", " / ".join(group), "合并为同一物理行，并用空行分隔不同自然段。"))
            continue
        raw = group[0]
        unsupported = _unsupported_issue(line_number, raw)
        if unsupported:
            issues.append(unsupported)
            continue
        if raw in {TITLE_START, TITLE_END, SIGNATURE_MARK}:
            issues.append(_issue(line_number, "E_DUPLICATE_MARKER", "结构标记出现在错误位置。", raw))
            continue
        if UNKNOWN_MARK_RE.match(raw):
            issues.append(_issue(line_number, "E_UNKNOWN_MARK", "存在未知边界标记。", raw, "删除未知标记或更新输入契约。"))
            continue

        h1_match = H1_RE.match(raw)
        h2_match = H2_RE.match(raw)
        h3_match = H3_RE.match(raw)
        if h1_match:
            number = chinese_number(h1_match.group(1))
            if number != expected_h1:
                issues.append(_issue(line_number, "E_H1_SEQUENCE", f"一级标题应为第 {expected_h1} 项。", raw, "修正中文序号并保持连续。"))
            expected_h1 += 1
            expected_h2 = 1
            expected_h3 = 1
            seen_h1 = True
            blocks.append(Block("heading1", raw[3:], line_number))
            continue
        if h2_match:
            if not seen_h1:
                issues.append(_issue(line_number, "E_LEVEL_JUMP", "二级标题之前缺少一级标题。", raw, "先添加所属一级标题。"))
                continue
            number = chinese_number(h2_match.group(1))
            if number != expected_h2:
                issues.append(_issue(line_number, "E_H2_SEQUENCE", f"当前一级标题下的二级标题应为第 {expected_h2} 项。", raw, "修正括号内中文序号并保持连续。"))
            expected_h2 += 1
            expected_h3 = 1
            blocks.append(Block("heading2", raw[4:], line_number))
            continue
        if h3_match:
            if not seen_h1:
                issues.append(_issue(line_number, "E_LEVEL_JUMP", "三级内容之前缺少一级标题。", raw, "先添加所属一级标题。"))
                continue
            number = int(h3_match.group(1))
            if number != expected_h3:
                issues.append(_issue(line_number, "E_H3_SEQUENCE", f"当前父级下的三级内容应从 {expected_h3}. 开始。", raw, "修正阿拉伯数字并保持连续。"))
            expected_h3 += 1
            blocks.append(Block("heading3", raw, line_number))
            continue
        if raw.startswith("#"):
            issues.append(_issue(line_number, "E_UNKNOWN_HEADING", "标题标记不符合输入契约。", raw, "一级使用 `## 一、`，二级使用 `### （一）`。"))
            continue
        if not seen_h1:
            issues.append(_issue(line_number, "E_BODY_BEFORE_H1", "主标题后必须先出现一级标题。", raw, "将正文放到对应一级标题之后。"))
            continue
        blocks.append(Block("paragraph", raw, line_number))

    if not blocks or not any(block.type == "heading1" for block in blocks):
        issues.append(_issue(title_end + 2, "E_NO_H1", "正文至少需要一个一级标题。", suggestion="添加 `## 一、……`。"))

    if issues:
        raise InputContractError(issues, source)

    return ProposalDocument(
        title_lines=tuple(title_lines),
        blocks=tuple(blocks),
        signature=Signature(tail[0], tail[1], signature_index + 1),
        source=source,
    )


def parse_file(path: str | Path) -> ProposalDocument:
    path = Path(path)
    return parse_text(path.read_text(encoding="utf-8-sig"), str(path.resolve()))
