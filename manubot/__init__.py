try:
    from .version import version as __version__
except ModuleNotFoundError:
    __version__ = "NA"

__all__ = ["__version__"]
