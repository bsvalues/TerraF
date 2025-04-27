from setuptools import setup, find_packages

setup(
    name="tf-bridge",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
    ],
    python_requires=">=3.8",
    description="TerraFusion Python-to-Node Bridge",
    author="TerraFusion Team",
    author_email="info@terrafusion.io",
)