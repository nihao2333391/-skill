from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from proposal_format.docx_builder import build_docx
from proposal_format.environment import check_environment
from proposal_format.parser import InputContractError, parse_file
from proposal_format.report import create_report, finalize_report
from proposal_format.verifier import all_passed, verify_docx


PROFILE_PATH = SKILL_ROOT / "references" / "format-profile.json"


def load_profile(path: Path = PROFILE_PATH) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def emit(payload: dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def parse_or_emit_error(input_path: Path):
    try:
        return parse_file(input_path)
    except FileNotFoundError:
        emit({"ok": False, "stage": "input", "errors": [{"line": 0, "code": "E_NOT_FOUND", "message": f"找不到输入文件：{input_path}"}]})
        raise SystemExit(2)
    except UnicodeDecodeError:
        emit({"ok": False, "stage": "input", "errors": [{"line": 0, "code": "E_ENCODING", "message": "输入文件必须使用 UTF-8 编码。"}]})
        raise SystemExit(2)
    except InputContractError as error:
        emit({"ok": False, "stage": "input", "source": error.source, "errors": [issue.as_dict() for issue in error.issues]})
        raise SystemExit(2)


def command_check(args: argparse.Namespace) -> int:
    input_path = Path(args.input).resolve()
    model = parse_or_emit_error(input_path)
    profile = load_profile()
    environment = check_environment(profile)
    emit(
        {
            "ok": environment.ok,
            "stage": "preflight",
            "input": str(input_path),
            "structure": model.counts(),
            "environment": environment.details,
            "errors": environment.errors,
        }
    )
    return 0 if environment.ok else 3


def _render_with_word(docx_path: Path, pdf_path: Path, powershell: str) -> dict[str, object]:
    script = SCRIPT_DIR / "render_with_word.ps1"
    process = subprocess.run(
        [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), "-InputDocx", str(docx_path), "-OutputPdf", str(pdf_path)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if process.returncode != 0:
        details = (process.stderr or process.stdout).strip()
        raise RuntimeError(f"Word 渲染失败（退出码 {process.returncode}）：{details}")
    lines = [line.strip() for line in process.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("Word 渲染脚本没有返回结果。")
    return json.loads(lines[-1])


def _render_pngs(pdf_path: Path, qa_dir: Path, pdftoppm: str) -> list[Path]:
    prefix = qa_dir / "page"
    subprocess.run(
        [pdftoppm, "-png", "-r", "180", str(pdf_path), str(prefix)],
        check=True,
        capture_output=True,
    )
    generated = sorted(qa_dir.glob("page-*.png"))
    renamed: list[Path] = []
    for index, source in enumerate(generated, start=1):
        target = qa_dir / f"page-{index:03d}.png"
        source.replace(target)
        renamed.append(target)
    return renamed


def command_build(args: argparse.Namespace) -> int:
    input_path = Path(args.input).resolve()
    model = parse_or_emit_error(input_path)
    profile = load_profile()
    environment = check_environment(profile)
    if not environment.ok:
        emit({"ok": False, "stage": "environment", "errors": environment.errors, "environment": environment.details})
        return 3

    output_dir = Path(args.output_dir).resolve()
    output_dir_existed = output_dir.exists()
    stem = input_path.stem
    docx_path = output_dir / f"{stem}.formatted.docx"
    report_path = output_dir / f"{stem}.format-report.md"
    qa_path = output_dir / "qa" / stem
    collisions = [path for path in (docx_path, report_path, qa_path) if path.exists()]
    if collisions:
        emit({"ok": False, "stage": "output", "errors": ["为避免覆盖现有结果，输出目标必须不存在。"], "collisions": [str(path) for path in collisions]})
        return 4

    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix=f".{stem}-", dir=output_dir) as temp_name:
            staging = Path(temp_name)
            staged_docx = staging / docx_path.name
            staged_qa = staging / "qa"
            staged_qa.mkdir()

            build_docx(model, profile, staged_docx)
            checks = verify_docx(staged_docx, model, profile)
            if not all_passed(checks):
                emit({"ok": False, "stage": "verification", "errors": [check.as_dict() for check in checks if not check.passed]})
                return 5

            rendered_pdf = staged_qa / "rendered.pdf"
            render_result = _render_with_word(staged_docx, rendered_pdf, str(environment.details["powershell"]))
            pages = _render_pngs(rendered_pdf, staged_qa, str(environment.details["pdftoppm"]))
            if not pages:
                raise RuntimeError("PDF 已生成，但没有得到页面 PNG。")
            word_pages = int(render_result.get("pages", 0))
            if word_pages and word_pages != len(pages):
                raise RuntimeError(f"Word 报告 {word_pages} 页，但渲染得到 {len(pages)} 张页面图片。")

            docx_path.parent.mkdir(parents=True, exist_ok=True)
            qa_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(staged_docx), str(docx_path))
            shutil.move(str(staged_qa), str(qa_path))
            create_report(
                report_path=report_path,
                input_path=input_path,
                output_path=docx_path,
                model=model,
                environment=environment,
                checks=checks,
                expected_pages=len(pages),
                word_version=str(render_result.get("word_version") or "未知"),
            )
    except (OSError, subprocess.SubprocessError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        if docx_path.exists():
            docx_path.unlink()
        if report_path.exists():
            report_path.unlink()
        if qa_path.exists():
            shutil.rmtree(qa_path)
        if not output_dir_existed and output_dir.exists() and not any(output_dir.iterdir()):
            output_dir.rmdir()
        emit({"ok": False, "stage": "generation", "errors": [str(error)]})
        return 4

    emit(
        {
            "ok": True,
            "stage": "awaiting_visual_review",
            "docx": str(docx_path),
            "report": str(report_path),
            "qa": str(qa_path),
            "pages": len(pages),
        }
    )
    return 0


def command_finalize(args: argparse.Namespace) -> int:
    report_path = Path(args.report).resolve()
    try:
        finalize_report(report_path, args.visual_status, args.pages, args.note or "")
    except (OSError, ValueError) as error:
        emit({"ok": False, "stage": "visual_review", "errors": [str(error)]})
        return 6
    emit({"ok": args.visual_status == "pass", "stage": "complete" if args.visual_status == "pass" else "visual_failed", "report": str(report_path), "pages": args.pages})
    return 0 if args.visual_status == "pass" else 6


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="将约定结构的策划案 Markdown 生成并核验为 DOCX。")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="检查输入结构和运行环境，不生成文件。")
    check.add_argument("input")
    check.set_defaults(func=command_check)

    build = subparsers.add_parser("build", help="生成 DOCX、核验报告和 Word 页面预览。")
    build.add_argument("input")
    build.add_argument("--output-dir", required=True)
    build.set_defaults(func=command_build)

    finalize = subparsers.add_parser("finalize-report", help="记录逐页视觉检查结果。")
    finalize.add_argument("report")
    finalize.add_argument("--visual-status", choices=("pass", "fail"), required=True)
    finalize.add_argument("--pages", type=int, required=True)
    finalize.add_argument("--note")
    finalize.set_defaults(func=command_finalize)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
