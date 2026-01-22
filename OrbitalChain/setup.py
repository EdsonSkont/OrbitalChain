"""
OrbitalChain: Truth Discovery Mechanisms for Dynamic Data Streams 
in Inter-Satellite Communication

This package provides privacy-preserving truth discovery and consensus
mechanisms for LEO satellite networks.
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    with open("README.md", "r", encoding="utf-8") as f:
        return f.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="orbitalchain",
    version="1.0.0",
    author="OrbitalChain Authors",
    author_email="your.email@university.edu",
    description="Privacy-preserving truth discovery for LEO satellite networks",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/OrbitalChain",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/OrbitalChain/issues",
        "Documentation": "https://github.com/yourusername/OrbitalChain/docs",
        "Source Code": "https://github.com/yourusername/OrbitalChain",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering",
        "Topic :: Security :: Cryptography",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=4.0.0",
        ],
        "docs": [
            "sphinx>=4.5.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "orbitalchain=src.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
