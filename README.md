# vid2gif

Convert a video (MP4, MOV, …) to an animated GIF. Every GIF parameter — frame
rate, size, palette, dithering, trimming, speed, loop — is driven by a config
file (YAML or JSON), with optional per-run CLI overrides.

Under the hood it uses ffmpeg's high-quality two-pass palette method
(`palettegen` + `paletteuse`) for crisp, well-dithered GIFs.

## Requirements

- [ffmpeg](https://ffmpeg.org/) on your `PATH` (or pass `--ffmpeg /path/to/ffmpeg`)
- Python 3.8+

## Install

```bash
pip install -e .
```

This adds a `vid2gif` command. (You can also run it without installing via
`python -m vid2gif.cli`.)

## Usage

```bash
# Defaults (480px wide, 15 fps, infinite loop)
vid2gif clip.mp4

# Explicit output path
vid2gif clip.mp4 out.gif

# Use a config file
vid2gif clip.mp4 out.gif --config config.example.yaml

# Override individual parameters (these win over the config file)
vid2gif clip.mp4 --fps 24 --width 600 --start 2 -t 5 --speed 1.5

# Inspect the effective config without converting
vid2gif clip.mp4 --config config.example.yaml --dump-config
```

If the output path is omitted, it defaults to the input name with a `.gif`
suffix (e.g. `clip.mp4` → `clip.gif`).

## Configuration

Copy [`config.example.yaml`](config.example.yaml) and edit it. Any omitted key
falls back to its default.

| Key           | Default      | Meaning                                           |
| ------------- | ------------ | ------------------------------------------------- |
| `fps`         | `15`         | Frames per second of the GIF                      |
| `start_time`  | `null`       | Seconds to seek before encoding                   |
| `duration`    | `null`       | Seconds of video to encode (`null` = to the end)  |
| `speed`       | `1.0`        | Playback speed multiplier (`2.0` = 2× faster)     |
| `reverse`     | `false`      | Play the clip backwards                           |
| `width`       | `480`        | Output width in px; `-1` keeps aspect ratio       |
| `height`      | `-1`         | Output height in px; `-1` keeps aspect ratio      |
| `scale_flags` | `lanczos`    | Scaler: `lanczos`, `bicubic`, `bilinear`, …       |
| `max_colors`  | `256`        | Palette size, 2–256 (fewer ⇒ smaller file)        |
| `stats_mode`  | `full`       | Palette generation: `full`, `diff`, `single`      |
| `dither`      | `sierra2_4a` | `none`, `bayer`, `floyd_steinberg`, `sierra2`, …  |
| `bayer_scale` | `3`          | 0–5, only used when `dither: bayer`               |
| `diff_mode`   | `none`       | `paletteuse` diff mode: `none`, `rectangle`       |
| `loop`        | `0`          | `0` = forever, `-1` = play once, `n` = repeat n   |
| `overwrite`   | `true`       | Overwrite the output file if it exists            |
| `loglevel`    | `error`      | ffmpeg log level                                  |

JSON config files (`.json`) are supported too and use the same keys.

## Python API

```python
from vid2gif import GifConfig, convert

cfg = GifConfig(fps=20, width=600, dither="bayer")
convert("clip.mp4", "clip.gif", cfg)

# or load from a file
cfg = GifConfig.from_file("config.example.yaml")
convert("clip.mp4", config=cfg)
```

## Tests

```bash
pip install -e ".[test]"
pytest
```
