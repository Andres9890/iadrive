from setuptools import setup, find_packages
from iadrive import __version__

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="iadrive",
    version=__version__,
    author="Andres99",
    author_email="fndres195@gmail.com",
    description="Download Google Drive files/folders and upload them to the Internet Archive",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Andres9890/iadrive",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "iadrive=iadrive.__main__:main",
        ],
    },
)