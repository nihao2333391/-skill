from __future__ import annotations

from dataclasses import dataclass, field
import importlib.util
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Iterable


@dataclass
class EnvironmentResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    details: dict[str, object] = field(default_factory=dict)


def _normalize_font_name(value: str) -> str:
    value = value.casefold()
    value = re.sub(r"\(.*?\)", "", value)
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]", "", value)


def collect_installed_font_tokens() -> set[str]:
    tokens: set[str] = set()
    if os.name == "nt":
        try:
            import winreg

            locations = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"),
            ]
            for hive, key_name in locations:
                try:
                    with winreg.OpenKey(hive, key_name) as key:
                        index = 0
                        while True:
                            try:
                                name, data, _ = winreg.EnumValue(key, index)
                            except OSError:
                                break
                            tokens.add(_normalize_font_name(str(name)))
                            tokens.add(_normalize_font_name(str(data)))
                            index += 1
                except OSError:
                    continue
        except ImportError:
            pass

    font_dir = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    if font_dir.is_dir():
        for item in font_dir.iterdir():
            tokens.add(_normalize_font_name(item.name))
            tokens.add(_normalize_font_name(item.stem))
    return {token for token in tokens if token}


def find_missing_fonts(required: Iterable[dict[str, object]], installed: set[str] | None = None) -> list[str]:
    installed = installed if installed is not None else collect_installed_font_tokens()
    missing: list[str] = []
    for font in required:
        aliases = [str(font["name"]), *[str(alias) for alias in font.get("aliases", [])]]
        normalized = [_normalize_font_name(alias) for alias in aliases]
        found = any(
            alias and any(alias in token for token in installed)
            for alias in normalized
        )
        if not found:
            missing.append(str(font["name"]))
    return missing


def find_word() -> Path | None:
    candidates: list[Path] = []
    if os.name == "nt":
        try:
            import winreg

            for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                try:
                    with winreg.OpenKey(hive, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\Winword.exe") as key:
                        candidates.append(Path(winreg.QueryValue(key, None)))
                except OSError:
                    pass
        except ImportError:
            pass
    candidates.extend(
        Path(path)
        for path in (
            r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
            r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE",
            r"C:\Program Files\Microsoft Office\Office16\WINWORD.EXE",
            r"C:\Program Files (x86)\Microsoft Office\Office16\WINWORD.EXE",
        )
    )
    return next((path for path in candidates if path.is_file()), None)


def find_pdftoppm() -> Path | None:
    discovered = shutil.which("pdftoppm") or shutil.which("pdftoppm.exe")
    if discovered:
        return Path(discovered)
    runtime_candidate = Path(sys.executable).resolve().parent.parent / "native" / "poppler" / "Library" / "bin" / "pdftoppm.exe"
    return runtime_candidate if runtime_candidate.is_file() else None


def check_environment(profile: dict[str, object]) -> EnvironmentResult:
    errors: list[str] = []
    details: dict[str, object] = {
        "platform": sys.platform,
        "python": sys.version.split()[0],
    }

    if importlib.util.find_spec("docx") is None:
        errors.append("缺少 python-docx，无法生成 DOCX。")

    word = find_word()
    details["word_path"] = str(word) if word else None
    if word is None:
        errors.append("未找到 Microsoft Word。")

    powershell = shutil.which("powershell.exe") or shutil.which("powershell")
    details["powershell"] = powershell
    if not powershell:
        errors.append("未找到 PowerShell，无法调用 Word 渲染。")

    pdftoppm = find_pdftoppm()
    details["pdftoppm"] = str(pdftoppm) if pdftoppm else None
    if pdftoppm is None:
        errors.append("未找到 pdftoppm，无法生成逐页预览。")

    required_fonts = profile["fonts"]["required"]
    missing = find_missing_fonts(required_fonts)
    details["required_fonts"] = [font["name"] for font in required_fonts]
    details["missing_fonts"] = missing
    if missing:
        errors.append("缺少规定字体：" + "、".join(missing) + "。")

    return EnvironmentResult(ok=not errors, errors=errors, details=details)
