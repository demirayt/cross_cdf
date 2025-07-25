from setuptools import setup, find_packages

setup(
    name="cross_cdf",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "jsonschema"
    ],
    entry_points={
        "console_scripts": [
            "validate-cdf=cross_cdf.__init__:main"
        ]
    },
    include_package_data=True,
    package_data={
        "cross_cdf": ["data/*.csv", "data/*.json"]
    },
    author="Your Name",
    description="CSV validator for CDF metadata",
)
