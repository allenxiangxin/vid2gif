"""Unit tests for vid2gif (no ffmpeg execution required)."""
import json

import pytest

from vid2gif import GifConfig, build_filter_complex
from vid2gif.converter import build_command


def test_defaults_validate():
    GifConfig().validate()  # should not raise


def test_from_dict_rejects_unknown_keys():
    with pytest.raises(ValueError, match="Unknown config option"):
        GifConfig.from_dict({"frames_per_second": 20})


def test_merge_ignores_none_and_applies_values():
    cfg = GifConfig().merge(fps=None, width=320, reverse=True)
    assert cfg.fps == 15          # untouched (None override skipped)
    assert cfg.width == 320
    assert cfg.reverse is True


@pytest.mark.parametrize(
    "field, value",
    [
        ("fps", 0),
        ("speed", 0),
        ("max_colors", 1),
        ("max_colors", 300),
        ("dither", "nope"),
        ("bayer_scale", 9),
        ("stats_mode", "bogus"),
    ],
)
def test_validate_rejects_bad_values(field, value):
    with pytest.raises(ValueError):
        GifConfig.from_dict({field: value})


def test_from_file_json(tmp_path):
    path = tmp_path / "cfg.json"
    path.write_text(json.dumps({"fps": 24, "width": 600, "dither": "bayer"}))
    cfg = GifConfig.from_file(path)
    assert (cfg.fps, cfg.width, cfg.dither) == (24, 600, "bayer")


def test_from_file_yaml(tmp_path):
    path = tmp_path / "cfg.yaml"
    path.write_text("fps: 12\nmax_colors: 128\nreverse: true\n")
    cfg = GifConfig.from_file(path)
    assert (cfg.fps, cfg.max_colors, cfg.reverse) == (12, 128, True)


def test_filter_complex_basic():
    fc = build_filter_complex(GifConfig())
    assert "fps=15" in fc
    assert "scale=480:-1:flags=lanczos" in fc
    assert "split [s0][s1]" in fc
    assert "palettegen=max_colors=256:stats_mode=full" in fc
    assert "paletteuse=dither=sierra2_4a" in fc


def test_filter_complex_speed_reverse_and_bayer():
    cfg = GifConfig(speed=2.0, reverse=True, dither="bayer", bayer_scale=4)
    fc = build_filter_complex(cfg)
    assert "setpts=PTS/2.0" in fc
    assert "reverse" in fc
    assert "bayer_scale=4" in fc


def test_build_command_includes_seek_and_loop():
    cfg = GifConfig(start_time=1.5, duration=3.0, loop=-1)
    cmd = build_command("in.mp4", "out.gif", cfg, "ffmpeg")
    assert cmd[:2] == ["ffmpeg", "-hide_banner"]
    assert "-ss" in cmd and cmd[cmd.index("-ss") + 1] == "1.5"
    assert "-t" in cmd and cmd[cmd.index("-t") + 1] == "3.0"
    assert cmd[cmd.index("-loop") + 1] == "-1"
    assert cmd[-1] == "out.gif"
