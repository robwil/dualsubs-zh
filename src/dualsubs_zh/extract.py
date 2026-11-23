"""Extract a single subtitle stream from a video with ffmpeg."""

from __future__ import annotations

import subprocess
from pathlib import Path


def extract_srt(video: Path, stream_index: int) -> str:
    """Return the stream at ``stream_index`` converted to SRT text."""
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-nostdin", "-i", str(video), "-map", f"0:{stream_index}", "-f", "srt", "-"],
        check=True,
        capture_output=True,
    )
    return out.stdout.decode("utf-8", errors="replace")
