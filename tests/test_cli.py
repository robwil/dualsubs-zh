from pathlib import Path

import pytest

from dualsubs_zh import cli


@pytest.fixture
def folder(tmp_path, sample_probe, en_srt, zh_srt):
    (tmp_path / "ep1.mkv").write_bytes(b"fake video 1")
    (tmp_path / "ep2.mkv").write_bytes(b"fake video 2")
    (tmp_path / "notes.txt").write_text("ignored")
    sub = tmp_path / "Season 2"
    sub.mkdir()
    (sub / "deep.mkv").write_bytes(b"not processed")
    calls = []

    def extract(video: Path, indices: list[int]) -> dict[int, str]:
        calls.append((video.name, tuple(indices)))
        return {i: en_srt if i == 5 else zh_srt for i in indices}

    deps = cli.Deps(probe=lambda _: sample_probe, extract=extract)
    return tmp_path, deps, calls


def run(folder, deps, *args):
    return cli.main([str(folder), *args], deps=deps)


def test_creates_sidecars_non_recursively(folder, capsys):
    path, deps, calls = folder
    assert run(path, deps) == 0
    out1 = path / "ep1.zh.dual.ass"
    assert out1.exists() and (path / "ep2.zh.dual.ass").exists()
    assert not (path / "Season 2" / "deep.zh.dual.ass").exists()
    text = out1.read_text(encoding="utf-8")
    assert text.startswith("[Script Info]\n; dualsubs-zh: v1 src=")
    assert "Style: ZH," in text and "各位同学" in text
    # One extraction (single read of the file) per video, covering both tracks.
    assert sorted(calls) == [("ep1.mkv", (5, 27)), ("ep2.mkv", (5, 27))]
    assert "2 created" in capsys.readouterr().out


def test_second_run_is_idempotent(folder, capsys):
    path, deps, calls = folder
    run(path, deps)
    before = (path / "ep1.zh.dual.ass").stat().st_mtime_ns
    calls.clear()
    assert run(path, deps) == 0
    assert calls == []
    assert (path / "ep1.zh.dual.ass").stat().st_mtime_ns == before
    assert "2 skipped" in capsys.readouterr().out


def test_changed_options_reported_outdated_then_force(folder, capsys):
    path, deps, _ = folder
    run(path, deps)
    capsys.readouterr()
    run(path, deps, "--zh-position", "bottom")
    assert "outdated" in capsys.readouterr().out
    run(path, deps, "--zh-position", "bottom", "--force")
    assert "2 created" in capsys.readouterr().out


def test_foreign_file_not_overwritten(folder, capsys):
    path, deps, _ = folder
    foreign = path / "ep1.zh.dual.ass"
    foreign.write_text("[Script Info]\nTitle: hand made\n", encoding="utf-8")
    run(path, deps)
    assert "not made by dualsubs-zh" in capsys.readouterr().out
    assert "hand made" in foreign.read_text(encoding="utf-8")


def test_dry_run_writes_nothing(folder, capsys):
    path, deps, calls = folder
    assert run(path, deps, "--dry-run") == 0
    assert not list(path.glob("*.ass"))
    assert calls == []
    assert "2 would create" in capsys.readouterr().out


def test_error_sets_exit_code(folder, capsys):
    path, deps, _ = folder

    def boom(video, indices):
        raise OSError("disk on fire")

    deps.extract = boom
    assert run(path, deps) == 1
    assert "disk on fire" in capsys.readouterr().out
    assert not list(path.glob("*.ass")) and not list(path.glob(".dualsubs-*"))


def test_not_a_directory(tmp_path):
    assert cli.main([str(tmp_path / "nope")], deps=cli.Deps()) == 2
