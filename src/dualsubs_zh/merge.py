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
    # "stacked": both lines at the bottom, one above the other.
    # "split": lower language at the bottom, upper language at the top of the screen.
    layout: str = "stacked"
    # Which language is the upper line. Viewers read the upper line first, so put
    # the language you want to focus on there (default: Chinese).
    en_first: bool = False
    zh_font: str = "Noto Sans CJK SC"
    en_font: str = "Arial"
    font_scale: float = 1.0
    # English is the support line by default, so it's a bit smaller (bilingual
    # subtitle convention is 75-85% of the main line).
    en_scale: float = 0.8


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

    if options.layout not in ("stacked", "split"):
        raise ValueError(f"layout must be 'stacked' or 'split', got {options.layout!r}")

    base = height * FONT_SIZE_FRAC * options.font_scale
    sizes = {"ZH": round(base), "EN": round(base * options.en_scale)}
    margin = round(height * MARGIN_FRAC)
    outline = max(1.0, round(height * OUTLINE_FRAC, 1))

    out = pysubs2.SSAFile()
    out.info["PlayResX"] = str(width)
    out.info["PlayResY"] = str(height)
    out.info["ScaledBorderAndShadow"] = "yes"
    out.info["WrapStyle"] = "0"

    upper, lower = ("EN", "ZH") if options.en_first else ("ZH", "EN")
    if options.layout == "split":
        upper_align, upper_marginv = pysubs2.Alignment.TOP_CENTER, margin
    else:
        # Fixed offset leaving room for two lines of the lower language, so the
        # upper line doesn't jump around as the lower one changes length.
        upper_align, upper_marginv = pysubs2.Alignment.BOTTOM_CENTER, margin + round(sizes[lower] * 2.4)
    placement = {
        lower: (pysubs2.Alignment.BOTTOM_CENTER, margin),
        upper: (upper_align, upper_marginv),
    }
    fonts = {"EN": options.en_font, "ZH": options.zh_font}
    colors = {"EN": pysubs2.Color(255, 255, 255), "ZH": ZH_COLOR}
    for name in ("EN", "ZH"):
        align, marginv = placement[name]
        out.styles[name] = pysubs2.SSAStyle(
            fontname=fonts[name], fontsize=sizes[name], primarycolor=colors[name], alignment=align,
            marginv=marginv, marginl=margin, marginr=margin, outline=outline, shadow=1,
        )

    for text, style in ((en_srt, "EN"), (zh_srt, "ZH")):
        for e in _clean(pysubs2.SSAFile.from_string(text, format_="srt")):
            e.style = style
            out.append(e)
    # Deterministic order: by start time, English before Chinese on ties.
    out.events.sort(key=lambda e: (e.start, e.style != "EN", e.end))
    return out
