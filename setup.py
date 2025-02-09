from setuptools import setup, find_packages

setup(
    name="callite",
    version="0.2.10",
    packages=find_packages(),

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
        ]
    }
)