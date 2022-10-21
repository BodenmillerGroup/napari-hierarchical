import os
from typing import Optional, Union

from napari.plugins.utils import get_potential_readers
from pluggy import HookimplMarker

from napari_bioimage.hookspecs import ReaderFunction

from ._reader import read_napari

PathLike = Union[str, os.PathLike]

available: bool = True
hookimpl = HookimplMarker("napari-bioimage")


@hookimpl
def napari_bioimage_get_reader(path: PathLike) -> Optional[ReaderFunction]:
    if available and get_potential_readers(str(path)):  # TODO fix infinite loop
        return read_napari
    return None


__all__ = [
    "available",
    "read_napari",
    "napari_bioimage_get_reader",
]
