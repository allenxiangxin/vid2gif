"""Convert a video (e.g. MP4) to a GIF using ffmpeg.

Uses the high-quality two-pass palette technique in a single ffmpeg
invocation: the decoded/scaled frames are split, ``palettegen`` builds an
optimal palette, and ``paletteuse`` maps the frames onto it with dithering.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Union

from .config import GifConfig

PathLike = Union[str, Path]


class ConversionError(RuntimeError):
    """Raised when ffmpeg is missing or the conversion fails."""


def _resolve_ffmpeg(ffmpeg: Optional[str]) -> str:
    exe = ffmpeg or "ffmpeg"
    resolved = shutil.which(exe)
    if resolved is None:
        raise ConversionError(
            f"Could not find ffmpeg executable '{exe}'. Install ffmpeg or pass "
            "its path via the `ffmpeg=` argument."
        )
    return resolved


def build_filter_complex(cfg: GifConfig) -> str:
    """Build the ``-filter_complex`` string for the two-pass palette method."""
    chain: List[str] = []
    if cfg.speed != 1.0:
        # Smaller PTS multiplier => faster playback.
        chain.append(f"setpts=PTS/{cfg.speed}")
    chain.append(f"fps={cfg.fps}")
    chain.append(f"scale={cfg.width}:{cfg.height}:flags={cfg.scale_flags}")
    if cfg.reverse:
        chain.append("reverse")
    common = ",".join(chain)

    palettegen = (
        f"palettegen=max_colors={cfg.max_colors}:stats_mode={cfg.stats_mode}"
    )

    use_opts = [f"dither={cfg.dither}"]
    if cfg.dither == "bayer":
        use_opts.append(f"bayer_scale={cfg.bayer_scale}")
    use_opts.append(f"diff_mode={cfg.diff_mode}")
    paletteuse = "paletteuse=" + ":".join(use_opts)

    return (
        f"[0:v] {common},split [s0][s1];"
        f"[s0] {palettegen} [p];"
        f"[s1][p] {paletteuse}"
    )


def build_command(
    input_path: PathLike,
    output_path: PathLike,
    cfg: GifConfig,
    ffmpeg_exe: str,
) -> List[str]:
    """Assemble the full ffmpeg argument list."""
    cmd: List[str] = [ffmpeg_exe, "-hide_banner", "-loglevel", cfg.loglevel]
    cmd.append("-y" if cfg.overwrite else "-n")
    # Seeking before -i is fast and keyframe-accurate enough for GIFs.
    if cfg.start_time is not None:
        cmd += ["-ss", str(cfg.start_time)]
    if cfg.duration is not None:
        cmd += ["-t", str(cfg.duration)]
    cmd += ["-i", str(input_path)]
    cmd += ["-filter_complex", build_filter_complex(cfg)]
    cmd += ["-loop", str(cfg.loop)]
    cmd.append(str(output_path))
    return cmd


def convert(
    input_path: PathLike,
    output_path: Optional[PathLike] = None,
    config: Optional[GifConfig] = None,
    *,
    ffmpeg: Optional[str] = None,
) -> Path:
    """Convert ``input_path`` to a GIF and return the output path.

    Args:
        input_path: Source video (mp4, mov, ...).
        output_path: Destination ``.gif``. Defaults to the input name with a
            ``.gif`` suffix.
        config: A :class:`GifConfig`; defaults are used when omitted.
        ffmpeg: Path to the ffmpeg binary (defaults to ``ffmpeg`` on PATH).
    """
    cfg = (config or GifConfig()).validate()
    input_path = Path(input_path)
    if not input_path.is_file():
        raise ConversionError(f"Input file not found: {input_path}")

    out = Path(output_path) if output_path else input_path.with_suffix(".gif")
    if out.exists() and not cfg.overwrite:
        raise ConversionError(
            f"Output already exists and overwrite is disabled: {out}"
        )
    out.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg_exe = _resolve_ffmpeg(ffmpeg)
    cmd = build_command(input_path, out, cfg, ffmpeg_exe)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise ConversionError(
            f"ffmpeg failed (exit {proc.returncode}).\n"
            f"command: {' '.join(cmd)}\n"
            f"{proc.stderr.strip()}"
        )
    return out
