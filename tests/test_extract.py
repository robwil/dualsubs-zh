import shutil
import subprocess
from pathlib import Path

import pytest

from dualsubs_zh.extract import extract_srts

FIXTURES = Path(__file__).parent / "fixtures"

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")


@pytest.fixture
def mkv(tmp_path):
    """Tiny MKV with a black video stream and two subtitle streams (indices 1 and 2)."""
    out = tmp_path / "tiny.mkv"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-nostdin", "-f", "lavfi", "-i", "color=black:s=64x36:d=7",
         "-i", str(FIXTURES / "en.srt"), "-i", str(FIXTURES / "zh.srt"),
         "-map", "0", "-map", "1", "-map", "2", "-c:v", "ffv1", "-c:s", "srt", str(out)],
        check=True, capture_output=True,
    )
    return out


def test_extracts_multiple_streams_in_one_call(mkv):
    texts = extract_srts(mkv, [1, 2])
    assert set(texts) == {1, 2}
    assert "Students, contemplate this." in texts[1]
    assert "各位同学可以思考一下" in texts[2]


def test_duplicate_indices_collapsed(mkv):
    assert set(extract_srts(mkv, [1, 1])) == {1}
