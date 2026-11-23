"""Extract subtitle streams from a video with ffmpeg."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


def extract_srts(video: Path, stream_indices: list[int]) -> dict[int, str]:
    """Return each requested stream converted to SRT text, keyed by stream index.

    Subtitle packets are interleaved through the whole container, so ffmpeg has to
    read the entire file regardless; doing all streams in one invocation means the
    file is read once instead of once per track.
    """
    indices = list(dict.fromkeys(stream_indices))
    with tempfile.TemporaryDirectory(prefix="dualsubs-") as tmp:
        cmd = ["ffmpeg", "-v", "error", "-nostdin", "-y", "-i", str(video)]
        outputs = {i: Path(tmp) / f"{i}.srt" for i in indices}
        for i, out in outputs.items():
            cmd += ["-map", f"0:{i}", "-f", "srt", str(out)]
        subprocess.run(cmd, check=True, capture_output=True)
        return {i: out.read_text(encoding="utf-8", errors="replace") for i, out in outputs.items()}
