"""Setuptools build script.

Metadata lives here (rather than in pyproject.toml's ``[project]`` table) so the
package installs on older pip/setuptools that predate PEP 621/PEP 660, while
still building fine with modern tooling.
"""
from setuptools import find_packages, setup

setup(
    name="vid2gif",
    version="0.1.0",
    description="Convert video (MP4, ...) to GIF via ffmpeg, configured by file.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    license="MIT",
    python_requires=">=3.8",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=["pyyaml>=5.1"],
    extras_require={"test": ["pytest>=6.0"]},
    entry_points={"console_scripts": ["vid2gif = vid2gif.cli:main"]},
)
