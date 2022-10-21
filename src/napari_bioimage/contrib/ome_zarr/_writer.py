import os
from typing import Union

from napari_bioimage.model import Image

PathLike = Union[str, os.PathLike]


def write_ome_zarr(path: PathLike, image: Image) -> None:
    raise NotImplementedError()  # TODO
