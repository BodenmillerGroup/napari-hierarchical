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
from .contrib import hdf5, imc, netcdf4, zarr

if hdf5.available:
    controller.pm.register(hdf5, name="napari-hierarchical-hdf5")
if imc.available:
    controller.pm.register(imc, name="napari-hierarchical-imc")
if netcdf4.available:
    controller.pm.register(netcdf4, name="napari-hierarchical-netcdf4")
if zarr.available:
    controller.pm.register(zarr, name="napari-hierarchical-zarr")

__all__ = [
    "controller",
    "HierarchicalController",
    "HierarchicalControllerException",
    "napari_get_reader",
]
