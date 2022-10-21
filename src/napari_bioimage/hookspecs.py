import os
from typing import Callable, Optional, Union

from pluggy import HookspecMarker

from .model import Image

PathLike = Union[str, os.PathLike]
ReaderFunction = Callable[[PathLike], Image]
WriterFunction = Callable[[PathLike, Image], None]

hookspec = HookspecMarker("napari-bioimage")


@hookspec(firstresult=True)
def napari_bioimage_get_reader(path: PathLike) -> Optional[ReaderFunction]:
    pass


@hookspec(firstresult=True)
def napari_bioimage_get_writer(
    path: PathLike, image: Image
) -> Optional[WriterFunction]:
    pass
