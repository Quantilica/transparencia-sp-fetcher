"""Coletor e conversor Lake Hive de remuneração dos servidores de SP."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("transparencia-sp-fetcher")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = ["__version__"]
