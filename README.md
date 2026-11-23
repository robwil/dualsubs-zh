# dualsubs-zh

Show **English and Simplified Chinese subtitles at the same time** in Jellyfin (or any player that renders ASS subtitles).

Most players, including the Jellyfin clients, only show one subtitle track at a time. `dualsubs-zh` reads the English and Simplified Chinese text tracks embedded in each video and merges them into one styled `.ass` sidecar file:

- English: white, at the bottom
- Simplified Chinese: pale yellow, stacked just above the English (or at the top of the screen with `--zh-position top`)

Your video files are never modified.

## Requirements

- `ffmpeg` and `ffprobe` on `PATH`
- [uv](https://docs.astral.sh/uv/) (or any Python 3.10+ environment with `pysubs2`)

## Usage

```bash
uv run dualsubs-zh "/media/tv/Some Show/Season 1"
```

For every `.mkv` / `.mp4` / `.m4v` directly in that folder (subfolders are not processed), this writes `<video name>.zh.dual.ass` next to the video. Jellyfin detects it as an external Chinese subtitle titled "dual". Rescan the library if it doesn't appear.

Options:

| Flag | Default | Meaning |
|---|---|---|
| `--zh-position bottom\|top` | `bottom` | Chinese stacked above English, or at the top of the screen |
| `--font NAME` | `Noto Sans CJK SC` | Font for the Chinese line |
| `--font-scale X` | `1.0` | Scale text size (base is 5.5% of video height) |
| `--jobs N`, `-j N` | `min(4, CPUs)` | Videos processed in parallel |
| `--dry-run` | | Show which tracks would be used without writing anything |
| `--force` | | Regenerate outdated sidecars / overwrite files not made by this tool |

Text size and margins are proportional to the video's resolution (480p to 4K, any aspect ratio).

### Safe to re-run

Each generated file stores a hash of its inputs: the selected tracks, the video's size and modification time, and the options. On re-runs, up-to-date files are skipped. If a file is outdated, it's reported and only regenerated with `--force`. Files the tool didn't create are never overwritten unless you pass `--force`. That makes it suitable for a cron job.

### Track selection

- **English:** a text track tagged `eng`/`en`. Forced tracks are skipped and SDH tracks are used only if nothing else is available.
- **Chinese:** a text track tagged `chi`/`zho`/`zh`. It must be marked Simplified in its title or language tag (`Simplified`, `简体`, `chs`, `zh-Hans`, `zh-CN`, ...). Anything marked Traditional is ignored. If there is exactly one unmarked Chinese track, it's used with a warning.
- Image-based subtitles (PGS/VobSub) can't be used. Those files are skipped with an explanation.

## Fonts

A sidecar `.ass` file can't embed fonts, so the player must have a font with Chinese characters installed. The default, `Noto Sans CJK SC`, ships with Android (including Android TV / Fire TV). If you see empty boxes instead of Chinese characters, pass a font your device has. For example, on macOS:

```bash
uv run dualsubs-zh --font "Hiragino Sans GB" /path/to/folder
```

If Jellyfin transcodes and burns in subtitles, set **Dashboard → Playback → Fallback font folder** to a folder containing a CJK font.

## Jellyfin client notes

ASS positioning needs a player that renders ASS properly (libass, mpv, VLC, or the Jellyfin web player). Jellyfin for Android TV 0.20+ includes an experimental libass option in its playback settings. Without it, the server may transcode and burn the subtitles in, which still works but is slower.

## Development

```bash
uv run pytest
```

The project pins public PyPI. If your machine sets a different default index (for example via `UV_DEFAULT_INDEX`), override it when updating the lock file:

```bash
UV_DEFAULT_INDEX=https://pypi.org/simple/ uv lock
```

## License

MIT
