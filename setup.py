from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="urbanclear-traffic-system",
    version="1.0.0",
    author="Traffic System Team",
    author_email="team@urbanclear.com",
    description="Comprehensive traffic management system with ML-powered analytics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/urbanclear/traffic-system",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.10.0",
            "flake8>=6.1.0",
            "mypy>=1.6.0",
            "bandit>=1.7.5",
            "safety>=2.3.0",
            "pre-commit>=3.5.0",
        ],
        "test": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "locust>=2.17.0",
            "testfixtures>=7.2.0",
            "factory-boy>=3.3.0",
            "responses>=0.23.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "traffic-api=src.api.main:main",
            "traffic-data-generator=src.data.mock_data_generator:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 