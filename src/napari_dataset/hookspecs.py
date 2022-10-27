import os
from typing import Callable, Optional, Union

from pluggy import HookspecMarker

from .model import Dataset

PathLike = Union[str, os.PathLike]
ReaderFunction = Callable[[PathLike], Dataset]
WriterFunction = Callable[[PathLike, Dataset], None]

hookspec = HookspecMarker("napari-dataset")


@hookspec(firstresult=True)
def napari_dataset_get_reader(path: PathLike) -> Optional[ReaderFunction]:
    pass


@hookspec(firstresult=True)
def napari_dataset_get_writer(
    path: PathLike, dataset: Dataset
) -> Optional[WriterFunction]:
    pass
