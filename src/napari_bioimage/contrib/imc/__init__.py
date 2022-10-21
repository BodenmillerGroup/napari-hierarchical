import os
from pathlib import Path
from typing import Optional, Union

from pluggy import HookimplMarker

from napari_bioimage.hookspecs import ReaderFunction

from ._reader import read_imc

try:
    import readimc
except ModuleNotFoundError:
    readimc = None


PathLike = Union[str, os.PathLike]

available = readimc is not None
hookimpl = HookimplMarker("napari-bioimage")


@hookimpl
def napari_bioimage_get_reader(path: PathLike) -> Optional[ReaderFunction]:
    if available and Path(path).suffix == ".mcd":
        return read_imc
    return None


__all__ = [
    "available",
    "read_imc",
    "napari_bioimage_get_reader",
]
