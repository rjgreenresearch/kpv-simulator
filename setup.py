from setuptools import setup, find_packages

setup(
    name="kpv-simulator",
    version="1.0.0",
    author="Robert J. Green",
    author_email="robert@rjgreenresearch.org",
    description=(
        "Key Person Vulnerability Simulator — "
        "MTS Research Programme Working Paper 5"
    ),
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/rjgreenresearch/kpv-simulator",
    packages=find_packages(),
    python_requires=">=3.10",
    entry_points={"console_scripts": ["kpvs=main:main"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
        "Intended Audience :: Science/Research",
    ],
)
