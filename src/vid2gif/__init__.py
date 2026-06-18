"""vid2gif: convert video (MP4, ...) to GIF via ffmpeg, configured by file."""
from .config import GifConfig
from .converter import ConversionError, build_filter_complex, convert

__version__ = "0.1.0"
__all__ = [
    "GifConfig",
    "ConversionError",
    "convert",
    "build_filter_complex",
    "__version__",
]
