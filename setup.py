import itertools
import pathlib
import re

import setuptools

directory = pathlib.Path(__file__).parent.resolve()

# version
init_path = directory.joinpath("manubot", "__init__.py")
text = init_path.read_text(encoding="utf-8-sig")
pattern = re.compile(r"^__version__ = ['\"]([^'\"]*)['\"]", re.MULTILINE)
version = pattern.search(text).group(1)

# long_description
readme_path = directory.joinpath("README.md")
long_description = readme_path.read_text(encoding="utf-8-sig")

# extra dependencies with an "all" option
extras_require = {
    "webpage": ["opentimestamps-client"],
    "dev": ["black", "flake8", "ghp-import", "portray", "pytest"],
}
extras_require["all"] = list(
    dict.fromkeys(itertools.chain.from_iterable(extras_require.values()))
)

setuptools.setup(
    # Package details
    name="manubot",
    version=version,
    url="https://github.com/manubot/manubot",
    project_urls={
        "Source": "https://github.com/manubot/manubot",
        "Documentation": "https://manubot.github.io/manubot",
        "Tracker": "https://github.com/manubot/manubot/issues",
        "Homepage": "https://manubot.org",
        "Publication": "https://greenelab.github.io/meta-review/",
    },
    description="Python utilities for Manubot: Manuscripts, open and automated",
    long_description_content_type="text/markdown",
    long_description=long_description,
    license="BSD 3-Clause",
    # Author details
    author="Daniel Himmelstein",
    author_email="daniel.himmelstein@gmail.com",
    # Package topics
    keywords="manuscript markdown publishing references citations",
    classifiers=[
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    packages=setuptools.find_packages(exclude=["tests"]),
    # Specify python version
    python_requires=">=3.6",
    # Run-time dependencies
    install_requires=[
        "errorhandler",
        "isbnlib",
        "jinja2",
        "jsonref",
        "jsonschema",
        "packaging",
        "pandas",
        "panflute",
        "pybase62",
        "pyyaml",
        "ratelimiter",
        "requests-cache",
        "requests",
        "toml",
    ],
    # Additional groups of dependencies
    extras_require=extras_require,
    # Create command line script
    entry_points={
        "console_scripts": [
            "manubot = manubot.command:main",
            "pandoc-manubot-cite = manubot.pandoc.cite_filter:main",
        ],
    },
    # Include package data files
    package_data={
        "manubot": [
            "cite/*.lua",
            "process/header-includes-template.html",
            "webpage/redirect-template.html",
        ]
    },
)
