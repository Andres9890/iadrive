from setuptools import setup, find_packages

# Read version from file instead of importing
def get_version():
    with open("iadrive/__init__.py", "r") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    raise RuntimeError("Unable to find version string.")

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="iadrive",
    version=get_version(),
    author="Andres99",
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
    install_requires=[
        "internetarchive>=5.5.0",
        "gdown>=5.2.0",
        "docopt-ng>=0.9.0",
        "python-dateutil>=2.9.0.post0",
    ],
    entry_points={
        "console_scripts": [
            "iadrive=iadrive.__main__:main",
        ],
    },
)