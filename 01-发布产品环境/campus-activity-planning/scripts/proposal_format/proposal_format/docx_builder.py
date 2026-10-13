from __future__ import annotations

from pathlib import Path
import re

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt

from .parser import ProposalDocument


ALIGNMENTS = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}


def _set_rfonts(rpr, east_asia: str, western: str) -> None:
    rfonts = rpr.rFonts
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    rfonts.set(qn("w:ascii"), western)
    rfonts.set(qn("w:hAnsi"), western)
    rfonts.set(qn("w:eastAsia"), east_asia)
    rfonts.set(qn("w:cs"), western)


def _set_run_format(run, settings: dict[str, object]) -> None:
    run.font.name = str(settings["font_western"])
    run.font.size = Pt(float(settings["size_pt"]))
    run.font.bold = bool(settings.get("bold", False))
    _set_rfonts(run._element.get_or_add_rPr(), str(settings["font_east_asia"]), str(settings["font_western"]))


def _add_styled_text(paragraph, text: str, settings: dict[str, object]):
    """Write digits in independent Times New Roman runs without changing text."""
    last_run = None
    for part in re.split(r"(\d+)", text):
        if not part:
            continue
        run = paragraph.add_run(part)
        run_settings = settings
        if part.isdigit():
            run_settings = {
                **settings,
                "font_east_asia": settings["font_western"],
            }
        _set_run_format(run, run_settings)
        last_run = run
    return last_run


def _set_outline_level(style, level: int) -> None:
    ppr = style._element.get_or_add_pPr()
    existing = ppr.find(qn("w:outlineLvl"))
    if existing is not None:
        ppr.remove(existing)
    outline = OxmlElement("w:outlineLvl")
    outline.set(qn("w:val"), str(level))
    ppr.append(outline)


def _configure_style(document: Document, settings: dict[str, object]):
    name = str(settings["word_style"])
    try:
        style = document.styles[name]
    except KeyError:
        style = document.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    style.font.name = str(settings["font_western"])
    style.font.size = Pt(float(settings["size_pt"]))
    style.font.bold = bool(settings.get("bold", False))
    _set_rfonts(style._element.get_or_add_rPr(), str(settings["font_east_asia"]), str(settings["font_western"]))

    fmt = style.paragraph_format
    fmt.alignment = ALIGNMENTS[str(settings["alignment"])]
    fmt.first_line_indent = Pt(float(settings["first_line_indent_pt"]))
    fmt.space_before = Pt(float(settings["space_before_pt"]))
    fmt.space_after = Pt(float(settings["space_after_pt"]))
    fmt.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    fmt.line_spacing = Pt(float(settings["line_spacing_pt"]))
    if "outline_level" in settings:
        _set_outline_level(style, int(settings["outline_level"]))
    return style


def _add_text_paragraph(document: Document, text: str, settings: dict[str, object]):
    paragraph = document.add_paragraph(style=str(settings["word_style"]))
    _add_styled_text(paragraph, text, settings)
    return paragraph


def _add_page_number(section, settings: dict[str, object], footer_distance_mm: float) -> None:
    section.footer_distance = Mm(footer_distance_mm)
    footer = section.footer
    paragraph = footer.paragraphs[0]
    paragraph.alignment = ALIGNMENTS[str(settings["alignment"])]
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)

    run_settings = {
        "font_east_asia": settings["font"],
        "font_western": settings["font"],
        "size_pt": settings["size_pt"],
        "bold": False,
    }
    left = paragraph.add_run(str(settings["left_mark"]))
    _set_run_format(left, run_settings)

    field_run = paragraph.add_run()
    _set_run_format(field_run, run_settings)
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = " PAGE "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    cached = OxmlElement("w:t")
    cached.text = str(settings.get("start", 1))
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    field_run._r.extend([begin, instruction, separate, cached, end])

    right = paragraph.add_run(str(settings["right_mark"]))
    _set_run_format(right, run_settings)


def build_docx(model: ProposalDocument, profile: dict[str, object], output_path: str | Path) -> Path:
    output_path = Path(output_path)
    document = Document()

    styles = profile["styles"]
    for style_settings in styles.values():
        _configure_style(document, style_settings)

    section = document.sections[0]
    page = profile["page"]
    section.page_width = Mm(float(page["width_mm"]))
    section.page_height = Mm(float(page["height_mm"]))
    section.top_margin = Mm(float(page["margin_top_mm"]))
    section.bottom_margin = Mm(float(page["margin_bottom_mm"]))
    section.left_margin = Mm(float(page["margin_left_mm"]))
    section.right_margin = Mm(float(page["margin_right_mm"]))

    title_settings = styles["title"]
    title = document.add_paragraph(style=str(title_settings["word_style"]))
    for index, line in enumerate(model.title_lines):
        run = _add_styled_text(title, line, title_settings)
        if index < len(model.title_lines) - 1:
            run.add_break(WD_BREAK.LINE)

    style_for_type = {
        "heading1": styles["heading1"],
        "heading2": styles["heading2"],
        "heading3": styles["heading3"],
        "paragraph": styles["body"],
    }
    for block in model.blocks:
        _add_text_paragraph(document, block.text, style_for_type[block.type])

    _add_text_paragraph(document, model.signature.organization, styles["signature"])
    _add_text_paragraph(document, model.signature.date, styles["signature"])
    _add_page_number(section, profile["page_number"], float(page["footer_distance_mm"]))

    document.core_properties.title = "\n".join(model.title_lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(output_path)
    return output_path
