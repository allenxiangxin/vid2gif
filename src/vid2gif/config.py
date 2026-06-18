"""Configuration for video-to-GIF conversion.

A :class:`GifConfig` holds every adjustable GIF parameter. It can be loaded
from a YAML or JSON file (:meth:`GifConfig.from_file`) and selectively
overridden (e.g. from CLI flags) via :meth:`GifConfig.merge`.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any, Dict, Optional, Union

try:  # PyYAML is optional; JSON configs work without it.
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

# Allowed values for the enum-like ffmpeg options, used by ``validate()``.
_DITHERS = {
    "none",
    "bayer",
    "heckbert",
    "floyd_steinberg",
    "sierra2",
    "sierra2_4a",
}
_STATS_MODES = {"full", "diff", "single"}
_DIFF_MODES = {"none", "rectangle"}


@dataclass
class GifConfig:
    """All adjustable GIF-conversion parameters with sensible defaults."""

    # --- Frame rate & timing ------------------------------------------------
    fps: int = 15
    start_time: Optional[float] = None  # seconds to seek before encoding
    duration: Optional[float] = None    # seconds to encode (None = to end)
    speed: float = 1.0                  # playback speed multiplier (2.0 = 2x)
    reverse: bool = False               # play the clip backwards

    # --- Sizing -------------------------------------------------------------
    width: int = 480                    # output width in px; -1 keeps aspect
    height: int = -1                    # output height in px; -1 keeps aspect
    scale_flags: str = "lanczos"        # ffmpeg scaler (lanczos = sharp)

    # --- Palette / quality --------------------------------------------------
    max_colors: int = 256               # palette size, 2..256
    stats_mode: str = "full"            # palettegen: full | diff | single
    dither: str = "sierra2_4a"          # paletteuse dithering algorithm
    bayer_scale: int = 3                # 0..5, only used when dither=bayer
    diff_mode: str = "none"             # paletteuse: none | rectangle

    # --- Output -------------------------------------------------------------
    loop: int = 0                       # 0=infinite, -1=play once, n=repeat n
    overwrite: bool = True              # overwrite an existing output file
    loglevel: str = "error"             # ffmpeg -loglevel

    # ------------------------------------------------------------------ load
    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "GifConfig":
        """Build a config from a mapping, rejecting unknown keys (typos)."""
        data = data or {}
        if not isinstance(data, dict):
            raise ValueError("Config must be a mapping of key: value pairs.")
        known = {f.name for f in fields(cls)}
        unknown = set(data) - known
        if unknown:
            raise ValueError(
                "Unknown config option(s): "
                + ", ".join(sorted(unknown))
                + f". Valid options: {', '.join(sorted(known))}."
            )
        cfg = cls(**data)
        cfg.validate()
        return cfg

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> "GifConfig":
        """Load config from a ``.yaml``/``.yml``/``.json`` file."""
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f"Config file not found: {path}")
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".json":
            data = json.loads(text) if text.strip() else {}
        else:
            if yaml is None:
                raise RuntimeError(
                    "PyYAML is required to read YAML configs "
                    "(`pip install pyyaml`), or use a .json file."
                )
            data = yaml.safe_load(text) or {}
        return cls.from_dict(data)

    # ------------------------------------------------------------- transform
    def merge(self, **overrides: Any) -> "GifConfig":
        """Return a copy with the given (non-``None``) overrides applied."""
        data = self.to_dict()
        for key, value in overrides.items():
            if value is None:
                continue
            if key not in data:
                raise ValueError(f"Unknown config option: {key}")
            data[key] = value
        return type(self).from_dict(data)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    # -------------------------------------------------------------- validate
    def validate(self) -> "GifConfig":
        """Sanity-check values, raising ``ValueError`` on bad input."""
        if self.fps <= 0:
            raise ValueError("fps must be a positive integer.")
        if self.speed <= 0:
            raise ValueError("speed must be greater than 0.")
        if self.width == 0 or self.height == 0:
            raise ValueError("width/height must be a positive px value or -1.")
        if not (2 <= self.max_colors <= 256):
            raise ValueError("max_colors must be between 2 and 256.")
        if self.dither not in _DITHERS:
            raise ValueError(
                f"dither must be one of {sorted(_DITHERS)}, got '{self.dither}'."
            )
        if not (0 <= self.bayer_scale <= 5):
            raise ValueError("bayer_scale must be between 0 and 5.")
        if self.stats_mode not in _STATS_MODES:
            raise ValueError(
                f"stats_mode must be one of {sorted(_STATS_MODES)}."
            )
        if self.diff_mode not in _DIFF_MODES:
            raise ValueError(
                f"diff_mode must be one of {sorted(_DIFF_MODES)}."
            )
        if self.start_time is not None and self.start_time < 0:
            raise ValueError("start_time must be >= 0.")
        if self.duration is not None and self.duration <= 0:
            raise ValueError("duration must be greater than 0.")
        return self
