"""Setup script for the tf-bridge package."""

from setuptools import setup, find_packages

setup(
    name="tf-bridge",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "requests>=2.25.0",
        "streamlit>=1.10.0",
    ],
)