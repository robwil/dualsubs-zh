"""Merge English and Chinese subtitles into one two-style ASS document."""

from __future__ import annotations

import re
from dataclasses import dataclass

import pysubs2

DEFAULT_WIDTH, DEFAULT_HEIGHT = 1920, 1080

# Sizes are fractions of the video height so output looks the same at 480p..4K.
FONT_SIZE_FRAC = 0.055
MARGIN_FRAC = 0.045
OUTLINE_FRAC = 0.0028

ZH_COLOR = pysubs2.Color(255, 235, 150)  # pale yellow, distinguishes ZH from EN

_FONT_TAG_RE = re.compile(r"\{\\(?:fn|c|1c|3c|fs)[^}]*\}")


@dataclass(frozen=True)
class MergeOptions:
    zh_position: str = "bottom"  # "bottom" (stacked above English) or "top" of screen
    zh_font: str = "Noto Sans CJK SC"
    en_font: str = "Arial"
    font_scale: float = 1.0


def _clean(subs: pysubs2.SSAFile) -> list[pysubs2.SSAEvent]:
    events = []
    for e in subs:
        if e.is_comment or not e.plaintext.strip():
            continue
        # SRT <font> tags become inline overrides that would fight our styles.
        e.text = _FONT_TAG_RE.sub("", e.text)
        events.append(e)
    return events


def build_dual(
    en_srt: str,
    zh_srt: str,
    width: int | None,
    height: int | None,
    options: MergeOptions = MergeOptions(),
) -> pysubs2.SSAFile:
    if not width or not height:
        width, height = DEFAULT_WIDTH, DEFAULT_HEIGHT

    size = round(height * FONT_SIZE_FRAC * options.font_scale)
    margin = round(height * MARGIN_FRAC)
    outline = max(1.0, round(height * OUTLINE_FRAC, 1))

    out = pysubs2.SSAFile()
    out.info["PlayResX"] = str(width)
    out.info["PlayResY"] = str(height)
    out.info["ScaledBorderAndShadow"] = "yes"
    out.info["WrapStyle"] = "0"

    common = dict(fontsize=size, outline=outline, shadow=1, marginl=margin, marginr=margin)
    out.styles["EN"] = pysubs2.SSAStyle(
        fontname=options.en_font, alignment=pysubs2.Alignment.BOTTOM_CENTER, marginv=margin, **common
    )
    if options.zh_position == "top":
        zh_align, zh_marginv = pysubs2.Alignment.TOP_CENTER, margin
    elif options.zh_position == "bottom":
        # Leave room for two lines of English beneath.
        zh_align, zh_marginv = pysubs2.Alignment.BOTTOM_CENTER, margin + round(size * 2.4)
    else:
        raise ValueError(f"zh_position must be 'top' or 'bottom', got {options.zh_position!r}")
    out.styles["ZH"] = pysubs2.SSAStyle(
        fontname=options.zh_font, alignment=zh_align, marginv=zh_marginv, primarycolor=ZH_COLOR, **common
    )

    for text, style in ((en_srt, "EN"), (zh_srt, "ZH")):
        for e in _clean(pysubs2.SSAFile.from_string(text, format_="srt")):
            e.style = style
            out.append(e)
    # Deterministic order: by start time, English before Chinese on ties.
    out.events.sort(key=lambda e: (e.start, e.style != "EN", e.end))
    return out
