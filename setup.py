from setuptools import setup, find_packages

setup(
    name="darwinia",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "streamlit>=1.30.0",
        "plotly>=5.18.0",
    ],
    python_requires=">=3.10",
)
