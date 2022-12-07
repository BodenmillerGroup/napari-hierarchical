try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

from ._controller import (
    HierarchicalController,
    HierarchicalControllerException,
    controller,
)
from ._reader import napari_get_reader
from .contrib import hdf5, imc, zarr

if hdf5.available:
    controller.pm.register(hdf5, name="napari-hierarchical-hdf5")
if imc.available:
    controller.pm.register(imc, name="napari-hierarchical-imc")
if zarr.available:
    controller.pm.register(zarr, name="napari-hierarchical-zarr")

__all__ = [
    "controller",
    "HierarchicalController",
    "HierarchicalControllerException",
    "napari_get_reader",
]
