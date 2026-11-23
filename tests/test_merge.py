import pysubs2
import pytest

from dualsubs_zh.merge import MergeOptions, build_dual


@pytest.mark.parametrize("w,h", [(854, 480), (1280, 720), (1920, 1080), (3840, 2160), (1920, 800)])
def test_playres_matches_video_and_scales_sizes(en_srt, zh_srt, w, h):
    subs = build_dual(en_srt, zh_srt, w, h)
    assert subs.info["PlayResX"] == str(w)
    assert subs.info["PlayResY"] == str(h)
    assert subs.styles["ZH"].fontsize == pytest.approx(h * 0.055, abs=1)
    assert subs.styles["EN"].fontsize == pytest.approx(h * 0.055 * 0.8, abs=1)


def test_missing_dimensions_fall_back_to_1080p(en_srt, zh_srt):
    subs = build_dual(en_srt, zh_srt, None, None)
    assert (subs.info["PlayResX"], subs.info["PlayResY"]) == ("1920", "1080")


def test_default_stacks_zh_above_smaller_en(en_srt, zh_srt):
    subs = build_dual(en_srt, zh_srt, 1920, 1080)
    en, zh = subs.styles["EN"], subs.styles["ZH"]
    assert en.alignment == zh.alignment == pysubs2.Alignment.BOTTOM_CENTER
    assert zh.marginv > en.marginv
    assert en.fontsize < zh.fontsize
    assert zh.fontname == "Noto Sans CJK SC"


def test_split_layout_puts_zh_at_top(en_srt, zh_srt):
    subs = build_dual(en_srt, zh_srt, 1920, 1080, MergeOptions(layout="split"))
    assert subs.styles["EN"].alignment == pysubs2.Alignment.BOTTOM_CENTER
    assert subs.styles["ZH"].alignment == pysubs2.Alignment.TOP_CENTER


def test_en_first_stacked_swaps_lines(en_srt, zh_srt):
    subs = build_dual(en_srt, zh_srt, 1920, 1080, MergeOptions(en_first=True))
    assert subs.styles["EN"].marginv > subs.styles["ZH"].marginv
    # Gap above the lower line is sized from the lower (Chinese) line.
    assert subs.styles["EN"].marginv - subs.styles["ZH"].marginv == round(subs.styles["ZH"].fontsize * 2.4)


def test_en_first_split_puts_en_at_top(en_srt, zh_srt):
    subs = build_dual(en_srt, zh_srt, 1920, 1080, MergeOptions(layout="split", en_first=True))
    assert subs.styles["EN"].alignment == pysubs2.Alignment.TOP_CENTER
    assert subs.styles["ZH"].alignment == pysubs2.Alignment.BOTTOM_CENTER


def test_en_scale_one_gives_equal_sizes(en_srt, zh_srt):
    subs = build_dual(en_srt, zh_srt, 1920, 1080, MergeOptions(en_scale=1.0))
    assert subs.styles["EN"].fontsize == subs.styles["ZH"].fontsize


def test_invalid_layout(en_srt, zh_srt):
    with pytest.raises(ValueError):
        build_dual(en_srt, zh_srt, 1920, 1080, MergeOptions(layout="left"))


def test_events_sorted_styled_and_cleaned(en_srt, zh_srt):
    subs = build_dual(en_srt, zh_srt, 1920, 1080)
    assert [e.style for e in subs] == ["EN", "ZH", "EN", "ZH"]
    assert all(a.start <= b.start for a, b in zip(subs, subs[1:]))
    assert "{\\i1}" in subs[2].text          # italics kept
    assert "\\c" not in subs[3].text          # <font color> override stripped
    assert subs[3].plaintext == "当你碰到像今天"


def test_custom_font_and_scale(en_srt, zh_srt):
    subs = build_dual(en_srt, zh_srt, 1920, 1080, MergeOptions(zh_font="Hiragino Sans GB", font_scale=0.8))
    assert subs.styles["ZH"].fontname == "Hiragino Sans GB"
    assert subs.styles["ZH"].fontsize == round(1080 * 0.055 * 0.8)
    assert subs.styles["EN"].fontsize == round(1080 * 0.055 * 0.8 * 0.8)
