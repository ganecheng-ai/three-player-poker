"""Setup script for three-player-poker"""
from setuptools import setup, find_packages

setup(
    name="three-player-poker",
    version="0.1.0",
    description="A classic Chinese Dou Dizhu (Three Player Poker) game",
    author="Ganecheng AI",
    author_email="ganecheng@example.com",
    url="https://github.com/ganecheng-ai/three-player-poker",
    packages=find_packages(),
    install_requires=[
        "pygame>=2.5.0",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "three-player-poker=src.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Games/Entertainment :: Board Games",
    ],
)
