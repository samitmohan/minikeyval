from setuptools import setup, find_packages

setup(
    name="pykv",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.70.0",
        "uvicorn>=0.15.0",
        "aiohttp>=3.8.0",
        "aiofiles>=0.8.0",
        "pydantic>=1.8.2",
    ],
    entry_points={
        'console_scripts': [
            'pykv-master=pykv.master.server:main',
            'pykv-volume=pykv.volume.server:main',
            'pykv-client=pykv.client.cli:main',
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A mini key-value store in Python",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pykv",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
) 