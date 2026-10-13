from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from pathlib import Path
import re
from typing import Iterable

from .environment import EnvironmentResult
from .parser import ProposalDocument
from .verifier import CheckResult


STATUS_START = "<!-- overall-status:start -->"
STATUS_END = "<!-- overall-status:end -->"
VISUAL_START = "<!-- visual-review:start -->"
VISUAL_END = "<!-- visual-review:end -->"


def file_sha256(path: str | Path) -> str:
    digest = sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _display(value: object) -> str:
    if value is None:
        return "未检测到"
    if isinstance(value, list):
        return "、".join(map(str, value)) if value else "无"
    return str(value)


def create_report(
    report_path: str | Path,
    input_path: str | Path,
    output_path: str | Path,
    model: ProposalDocument,
    environment: EnvironmentResult,
    checks: Iterable[CheckResult],
    expected_pages: int,
    word_version: str | None,
) -> Path:
    report_path = Path(report_path)
    checks = list(checks)
    counts = model.counts()
    lines = [
        "# 策划案格式核验报告",
        "",
        "## 总体状态",
        "",
        f"{STATUS_START}等待视觉检查{STATUS_END}",
        "",
        "## 输入与输出",
        "",
        f"- 输入文件：`{Path(input_path).resolve()}`",
        f"- 输入 SHA-256：`{file_sha256(input_path)}`",
        f"- 输出文件：`{Path(output_path).resolve()}`",
        f"- 生成时间：{datetime.now().astimezone().isoformat(timespec='seconds')}",
        "",
        "## 环境检查",
        "",
        f"- Microsoft Word：{_display(environment.details.get('word_path'))}",
        f"- Word 版本：{_display(word_version)}",
        f"- 缺失字体：{_display(environment.details.get('missing_fonts'))}",
        f"- pdftoppm：{_display(environment.details.get('pdftoppm'))}",
        f"- 环境状态：{'通过' if environment.ok else '失败'}",
        "",
        "## 结构统计",
        "",
        "| 对象 | 数量 |",
        "|---|---:|",
        f"| 主标题行 | {counts['title_lines']} |",
        f"| 一级标题 | {counts['heading1']} |",
        f"| 二级标题 | {counts['heading2']} |",
        f"| 三级内容 | {counts['heading3']} |",
        f"| 普通正文 | {counts['paragraph']} |",
        f"| 落款 | {counts['signature']} |",
        "",
        "## 机器核验",
        "",
        "| 检查项 | 结果 | 期望 | 实际 |",
        "|---|---|---|---|",
    ]
    for check in checks:
        expected = str(check.expected).replace("|", "\\|").replace("\n", " ↵ ")
        actual = str(check.actual).replace("|", "\\|").replace("\n", " ↵ ")
        lines.append(f"| `{check.name}` | {'通过' if check.passed else '失败'} | {expected} | {actual} |")
    lines.extend(
        [
            "",
            f"<!-- expected-pages:{expected_pages} -->",
            VISUAL_START,
            "## Word 页面检查",
            "",
            "- 状态：等待视觉检查",
            f"- 应检查页数：{expected_pages}",
            "- 已检查页数：0",
            "- 说明：尚未逐页确认。",
            VISUAL_END,
            "",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def finalize_report(path: str | Path, status: str, pages: int, note: str = "") -> Path:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    expected_match = re.search(r"<!-- expected-pages:(\d+) -->", text)
    if not expected_match:
        raise ValueError("报告缺少 expected-pages 元数据。")
    expected_pages = int(expected_match.group(1))
    if pages < 1:
        raise ValueError("已检查页数必须大于 0。")
    if status == "pass" and pages != expected_pages:
        raise ValueError(f"通过时必须检查全部 {expected_pages} 页，实际提交 {pages} 页。")

    overall = "通过" if status == "pass" else "失败"
    visual = "通过" if status == "pass" else "失败"
    explanation = note.strip() or ("全部页面已经检查。" if status == "pass" else "页面检查发现问题。")
    text = re.sub(
        re.escape(STATUS_START) + r".*?" + re.escape(STATUS_END),
        f"{STATUS_START}{overall}{STATUS_END}",
        text,
        flags=re.DOTALL,
    )
    visual_block = "\n".join(
        [
            VISUAL_START,
            "## Word 页面检查",
            "",
            f"- 状态：{visual}",
            f"- 应检查页数：{expected_pages}",
            f"- 已检查页数：{pages}",
            f"- 说明：{explanation}",
            VISUAL_END,
        ]
    )
    text = re.sub(
        re.escape(VISUAL_START) + r".*?" + re.escape(VISUAL_END),
        visual_block,
        text,
        flags=re.DOTALL,
    )
    path.write_text(text, encoding="utf-8")
    return path
