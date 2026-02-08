import os
from setuptools import setup, find_packages

USE_CYTHON = os.environ.get("USE_CYTHON", "1") != "0"

ext_modules = []
if USE_CYTHON:
    try:
        from Cython.Build import cythonize

        ext_modules = cythonize(
            [
                "callite/**/*.py",
            ],
            compiler_directives={
                "language_level": "3",
                "boundscheck": False,
                "wraparound": False,
            },
            exclude=[
                "callite/__init__.py",
                "callite/client/__init__.py",
                "callite/server/__init__.py",
                "callite/rpctypes/__init__.py",
                "callite/shared/__init__.py",
            ],
        )
    except ImportError:
        print("Cython not found. Building pure Python package.")
        ext_modules = []

setup(
    name="callite",
    version="0.2.11",
    packages=find_packages(),
    ext_modules=ext_modules,

    # Metadata
    author="Emrah Gozcu",
    author_email="gozcu@gri.ai",
    description="Slim Redis RPC implementation",
    long_description=open('README.md').read(),
    url="https://github.com/gri-ai/callite",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License"
    ],

    # Dependencies
    install_requires=[
        "redis>=5.0.3",
    ],

    # Dev dependencies
    extras_require={
        'dev': [
            'mypy>=1.9.0',
            'setuptools>=69.1.1',
            'Cython>=3.0.0',
        ]
    }
)
