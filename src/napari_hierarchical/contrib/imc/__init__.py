import os
from pathlib import Path
from typing import Optional, Union

from pluggy import HookimplMarker

from napari_hierarchical.contrib.imc.model import IMCAcquisitionArray, IMCPanoramaArray
from napari_hierarchical.hookspecs import ArrayLoaderFunction, GroupReaderFunction
from napari_hierarchical.model import Array

from ._reader import load_imc_acquisition_array, load_imc_panorama_array, read_imc_group

try:
    import readimc
except ModuleNotFoundError:
    readimc = None


PathLike = Union[str, os.PathLike]

available = readimc is not None
hookimpl = HookimplMarker("napari-hierarchical")


@hookimpl
def napari_hierarchical_get_group_reader(
    path: PathLike,
) -> Optional[GroupReaderFunction]:
    if available and Path(path).suffix.lower() == ".mcd":
        return read_imc_group
    return None


@hookimpl
def napari_hierarchical_get_array_loader(array: Array) -> Optional[ArrayLoaderFunction]:
    if available and isinstance(array, IMCPanoramaArray):
        return load_imc_panorama_array
    if available and isinstance(array, IMCAcquisitionArray):
        return load_imc_acquisition_array
    return None


__all__ = [
    "available",
    "read_imc_group",
    "load_imc_panorama_array",
    "load_imc_acquisition_array",
    "napari_hierarchical_get_group_reader",
    "napari_hierarchical_get_array_loader",
]
