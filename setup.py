"""
GestureMouse AI - Setup & Distribution Configuration
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="gesturemouse-ai",
    version="1.0.0",
    author="Saiteja Allari",
    description="AI-Powered Hand Gesture Controlled Virtual Mouse & Fruit Ninja Arcade Game",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Saiteja-033/GestureMouse-AI",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Microsoft :: Windows",
        "Topic :: Scientific/Engineering :: Human Machine Interfaces",
        "Topic :: Games/Entertainment :: Arcade",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "gesturemouse=main:main",
        ],
    },
    include_package_data=True,
)
