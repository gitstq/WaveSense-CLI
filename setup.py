#!/usr/bin/env python3
"""
WaveSense-CLI Setup
安装配置
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="wavesense-cli",
    version="1.0.0",
    author="WaveSense Team",
    author_email="wavesense@example.com",
    description="Lightweight Wi-Fi CSI Motion Detection Engine",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gitstq/WaveSense-CLI",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Networking :: Monitoring",
        "Topic :: Home Automation",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "wavesense=main:main",
        ],
    },
    keywords=[
        "wifi",
        "csi",
        "channel-state-information",
        "motion-detection",
        "presence-sensing",
        "smart-home",
        "home-assistant",
        "iot",
        "wireless",
        "sensor"
    ],
    project_urls={
        "Bug Reports": "https://github.com/gitstq/WaveSense-CLI/issues",
        "Source": "https://github.com/gitstq/WaveSense-CLI",
    },
)
