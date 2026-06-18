"""Command-line interface for vid2gif."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .config import GifConfig
from .converter import ConversionError, convert

# CLI flag -> GifConfig field. These override values loaded from --config.
_OVERRIDE_FIELDS = (
    "fps",
    "width",
    "height",
    "start_time",
    "duration",
    "speed",
    "reverse",
    "max_colors",
    "dither",
    "loop",
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="vid2gif",
        description="Convert a video (e.g. MP4) to an animated GIF.",
    )
    p.add_argument("input", help="input video file, e.g. clip.mp4")
    p.add_argument(
        "output",
        nargs="?",
        help="output .gif (default: input name with a .gif suffix)",
    )
    p.add_argument(
        "-c", "--config", metavar="FILE",
        help="YAML or JSON config file with GIF parameters",
    )

    # Per-parameter overrides (take precedence over the config file).
    o = p.add_argument_group("parameter overrides")
    o.add_argument("--fps", type=int, help="frames per second (default 15)")
    o.add_argument("--width", type=int, help="output width px; -1 keeps aspect")
    o.add_argument("--height", type=int, help="output height px; -1 keeps aspect")
    o.add_argument("--start", dest="start_time", type=float, metavar="SEC",
                   help="seek to this time before encoding")
    o.add_argument("-t", "--duration", type=float, metavar="SEC",
                   help="seconds of video to encode")
    o.add_argument("--speed", type=float, help="playback speed multiplier")
    o.add_argument("--reverse", action="store_true", default=None,
                   help="play the clip backwards")
    o.add_argument("--max-colors", dest="max_colors", type=int,
                   help="palette size, 2..256 (default 256)")
    o.add_argument("--dither",
                   help="dither: none|bayer|floyd_steinberg|sierra2|sierra2_4a")
    o.add_argument("--loop", type=int,
                   help="0=infinite, -1=play once, n=repeat n times")

    p.add_argument("--ffmpeg", metavar="PATH", help="path to the ffmpeg binary")
    p.add_argument("--dump-config", action="store_true",
                   help="print the effective config and exit (no conversion)")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        cfg = GifConfig.from_file(args.config) if args.config else GifConfig()
        overrides = {f: getattr(args, f) for f in _OVERRIDE_FIELDS}
        cfg = cfg.merge(**overrides)
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        print(f"vid2gif: config error: {exc}", file=sys.stderr)
        return 2

    if args.dump_config:
        for key, value in cfg.to_dict().items():
            print(f"{key}: {value}")
        return 0

    output = args.output or str(Path(args.input).with_suffix(".gif"))
    try:
        result = convert(args.input, output, cfg, ffmpeg=args.ffmpeg)
    except ConversionError as exc:
        print(f"vid2gif: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {result}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
