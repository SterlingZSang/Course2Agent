"""Compatibility shim for editable installs with older pip versions."""

from setuptools import find_packages, setup


setup(
    name="course2agent",
    version="0.1.0",
    description="Turn course materials into a cited course skill and retrieval MCP server.",
    package_dir={"": "src"},
    packages=find_packages("src"),
    python_requires=">=3.10",
    extras_require={"pdf": ["pypdf>=5"]},
    entry_points={"console_scripts": ["course2agent=course2agent.cli:main"]},
)
