import pathlib
import re

import setuptools

directory = pathlib.Path(__file__).parent.resolve()

# version
init_path = directory.joinpath("manubot", "__init__.py")
text = init_path.read_text(encoding="utf-8-sig")
pattern = re.compile(r"^__version__ = ['\"]([^'\"]*)['\"]", re.MULTILINE)
version = pattern.search(text).group(1)

setuptools.setup(version=version)
