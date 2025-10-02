"""Setup script for EDR printing package."""

from setuptools import setup, find_packages

setup(
    name="edr-printing",
    version="1.0.0",
    description="EDR printing capabilities extracted from product-connections-manager",
    author="Extracted from product-connections-manager",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "typing-extensions>=4.5.0",
        "reportlab>=4.0.0",
    ],
    extras_require={
        "full": ["weasyprint>=60.0"],
    },
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)