"""
WaveSense-CLI - 安装配置 / Installation Configuration
======================================================

使用 python setup.py install 安装。
Install with: python setup.py install
"""

from setuptools import setup, find_packages

# 读取README（如果存在）/ Read README (if exists)
try:
    with open("README.md", "r", encoding="utf-8") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "WaveSense-CLI - Lightweight Terminal Wireless Signal Intelligence & Analysis Engine"

setup(
    name="wavesense-cli",
    version="1.0.0",
    description="轻量级终端无线信号智能感知与分析引擎 / Lightweight Terminal Wireless Signal Intelligence & Analysis Engine",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="WaveSense-CLI Contributors",
    license="MIT",
    url="https://github.com/wavesense-cli/wavesense-cli",
    packages=find_packages(exclude=["tests*", "docs*", "examples*"]),
    python_requires=">=3.7",
    # 零外部依赖 / Zero external dependencies
    install_requires=[],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "mypy>=1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "wavesense=wavesense_cli.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Networking",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
)
