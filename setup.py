import pathlib
import re

import setuptools

directory = pathlib.Path(__file__).parent.resolve()

# version
init_path = directory.joinpath('manubot', '__init__.py')
text = init_path.read_text()
pattern = re.compile(r"^__version__ = ['\"]([^'\"]*)['\"]", re.MULTILINE)
version = pattern.search(text).group(1)

# long_description
readme_path = directory.joinpath('README.md')
long_description = readme_path.read_text()

setuptools.setup(
    # Package details
    name='manubot',
    version=version,
    url='https://github.com/greenelab/manubot',
    description='Manuscript bot for automated scientific publishing',
    long_description_content_type='text/markdown',
    long_description=long_description,
    license='BSD 3-Clause',

    # Author details
    author='Daniel Himmelstein',
    author_email='daniel.himmelstein@gmail.com',

    # Package topics
    keywords='manuscript markdown publishing references citations',
    classifiers=[
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
    ],

    packages=setuptools.find_packages(
        exclude=['tests']
    ),

    # Specify python version
    python_requires='>=3.6',

    # Run-time dependencies
    install_requires=[
        'errorhandler',
        'isbnlib',
        'jinja2',
        'jsonref',
        'jsonschema',
        'pandas',
        'pybase62',
        'pyyaml',
        'ratelimiter',
        'requests-cache',
        'requests',
    ],

    # Additional groups of dependencies
    extras_require={
    },

    # Create command line script
    entry_points={
        'console_scripts': [
            'manubot = manubot.command:main',
        ],
    },

    # Include package data files from MANIFEST.in
    include_package_data=True,
)
