"""Read stream info with ffprobe and choose the English and Simplified Chinese tracks."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

TEXT_CODECS = {"subrip", "srt", "ass", "ssa", "webvtt", "mov_text", "text"}

EN_LANGS = {"eng", "en"}
ZH_LANGS = {"chi", "zho", "zh", "cmn", "zh-cn", "zh-hans", "zh-tw", "zh-hant", "zh-hk"}

SIMPLIFIED_RE = re.compile(r"simplified|简体|简|chs|hans|zh-cn|zh_cn|\bsc\b|mandarin \(prc\)", re.I)
TRADITIONAL_RE = re.compile(r"traditional|繁|cht|hant|zh-tw|zh_tw|zh-hk|\btc\b", re.I)
SDH_RE = re.compile(r"\bsdh\b|\bcc\b|hearing", re.I)
FORCED_RE = re.compile(r"forced", re.I)


@dataclass(frozen=True)
class SubTrack:
    index: int
    codec: str
    language: str
    title: str
    forced: bool
    hearing_impaired: bool

    @property
    def is_text(self) -> bool:
        return self.codec in TEXT_CODECS

    @property
    def label(self) -> str:
        return f"#{self.index} {self.language} {self.title!r}".strip()


@dataclass(frozen=True)
class MediaInfo:
    width: int | None
    height: int | None
    subtitles: list[SubTrack]


@dataclass(frozen=True)
class Selection:
    english: SubTrack
    chinese: SubTrack
    warnings: tuple[str, ...] = ()


class SelectionError(Exception):
    """No suitable track pair was found; message says why."""


def run_ffprobe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", str(path)],
        check=True,
        capture_output=True,
    )
    return json.loads(out.stdout)


def parse_media_info(data: dict) -> MediaInfo:
    width = height = None
    subs: list[SubTrack] = []
    for s in data.get("streams", []):
        kind = s.get("codec_type")
        if kind == "video" and width is None and not s.get("disposition", {}).get("attached_pic"):
            width, height = s.get("width"), s.get("height")
        elif kind == "subtitle":
            tags = {k.lower(): v for k, v in (s.get("tags") or {}).items()}
            disp = s.get("disposition") or {}
            title = tags.get("title", "") or ""
            subs.append(
                SubTrack(
                    index=int(s["index"]),
                    codec=(s.get("codec_name") or "").lower(),
                    language=(tags.get("language") or "").lower(),
                    title=title,
                    forced=bool(disp.get("forced")) or bool(FORCED_RE.search(title)),
                    hearing_impaired=bool(disp.get("hearing_impaired")) or bool(SDH_RE.search(title)),
                )
            )
    return MediaInfo(width=width, height=height, subtitles=subs)


def _ranked(tracks: list[SubTrack]) -> list[SubTrack]:
    # Prefer non-SDH, then lowest stream index (usually the "main" track).
    return sorted(tracks, key=lambda t: (t.hearing_impaired, t.index))


def select_tracks(info: MediaInfo) -> Selection:
    subs = [t for t in info.subtitles if not t.forced]
    warnings: list[str] = []

    en = [t for t in subs if t.language in EN_LANGS]
    en_text = [t for t in en if t.is_text]
    if not en_text:
        raise SelectionError("no English text track" + (" (bitmap only)" if en else ""))

    zh = [t for t in subs if t.language in ZH_LANGS]
    zh_text = [t for t in zh if t.is_text]
    if not zh_text:
        raise SelectionError("no Chinese text track" + (" (bitmap only)" if zh else ""))

    def tag_text(t: SubTrack) -> str:
        return f"{t.language} {t.title}"

    simplified = [t for t in zh_text if SIMPLIFIED_RE.search(tag_text(t)) and not TRADITIONAL_RE.search(tag_text(t))]
    if simplified:
        chinese = _ranked(simplified)[0]
    else:
        untagged = [t for t in zh_text if not TRADITIONAL_RE.search(tag_text(t))]
        if len(untagged) == 1:
            chinese = untagged[0]
            warnings.append(f"Chinese track {chinese.label} not marked Simplified; using it anyway")
        elif not untagged:
            raise SelectionError("only Traditional Chinese text tracks found")
        else:
            raise SelectionError(
                "several Chinese tracks, none marked Simplified: " + ", ".join(t.label for t in untagged)
            )

    return Selection(english=_ranked(en_text)[0], chinese=chinese, warnings=tuple(warnings))
