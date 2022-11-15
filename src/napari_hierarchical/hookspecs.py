import os
from typing import Callable, Optional, Union

from pluggy import HookspecMarker

from .model import Array, Group

PathLike = Union[str, os.PathLike]
GroupReaderFunction = Callable[[PathLike], Group]
GroupWriterFunction = Callable[[PathLike, Group], None]
ArrayLoaderFunction = Callable[[Array], None]
ArraySaverFunction = Callable[[Array], None]

hookspec = HookspecMarker("napari-hierarchical")


@hookspec(firstresult=True)
def napari_hierarchical_get_group_reader(
    path: PathLike,
) -> Optional[GroupReaderFunction]:
    pass


@hookspec(firstresult=True)
def napari_hierarchical_get_group_writer(
    path: PathLike, group: Group
) -> Optional[GroupWriterFunction]:
    pass


@hookspec(firstresult=True)
def napari_hierarchical_get_array_loader(array: Array) -> Optional[ArrayLoaderFunction]:
    pass


@hookspec(firstresult=True)
def napari_hierarchical_get_array_saver(array: Array) -> Optional[ArraySaverFunction]:
    pass
