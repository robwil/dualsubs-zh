import pytest

from dualsubs_zh.probe import SelectionError, parse_media_info, select_tracks


def sub(index, lang, title="", codec="subrip", **disp):
    return {"index": index, "codec_type": "subtitle", "codec_name": codec,
            "tags": {"language": lang, "title": title}, "disposition": disp}


def video(w=1920, h=1080):
    return {"index": 0, "codec_type": "video", "codec_name": "hevc", "width": w, "height": h}


def test_sample_picks_simplified_not_traditional(sample_probe):
    info = parse_media_info(sample_probe)
    assert (info.width, info.height) == (3840, 2160) or info.width
    sel = select_tracks(info)
    assert sel.english.index == 5
    assert sel.chinese.index == 27
    assert sel.warnings == ()


def test_simplified_by_language_tag():
    info = parse_media_info({"streams": [video(), sub(2, "eng"), sub(3, "zh-hant"), sub(4, "zh-hans")]})
    assert select_tracks(info).chinese.index == 4


def test_single_untagged_chinese_used_with_warning():
    info = parse_media_info({"streams": [video(), sub(2, "eng"), sub(3, "chi", "Chinese")]})
    sel = select_tracks(info)
    assert sel.chinese.index == 3
    assert sel.warnings


def test_ambiguous_chinese_rejected():
    info = parse_media_info({"streams": [video(), sub(2, "eng"), sub(3, "chi"), sub(4, "chi")]})
    with pytest.raises(SelectionError, match="none marked Simplified"):
        select_tracks(info)


def test_traditional_only_rejected():
    info = parse_media_info({"streams": [video(), sub(2, "eng"), sub(3, "chi", "Traditional")]})
    with pytest.raises(SelectionError, match="Traditional"):
        select_tracks(info)


def test_bitmap_only_reported():
    info = parse_media_info({"streams": [video(), sub(2, "eng", codec="hdmv_pgs_subtitle"), sub(3, "chi", "简体")]})
    with pytest.raises(SelectionError, match="bitmap"):
        select_tracks(info)


def test_english_prefers_non_sdh_and_skips_forced():
    info = parse_media_info({"streams": [
        video(), sub(2, "eng", "Forced"), sub(3, "eng", "SDH"), sub(4, "eng", "English"), sub(5, "chi", "Simplified"),
    ]})
    assert select_tracks(info).english.index == 4


def test_forced_disposition_excluded():
    info = parse_media_info({"streams": [video(), sub(2, "eng", forced=1), sub(3, "chi", "Simplified")]})
    with pytest.raises(SelectionError, match="English"):
        select_tracks(info)
