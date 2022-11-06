try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

from ._controller import DatasetController, DatasetControllerException, controller
from ._reader import napari_get_reader
from .contrib import hdf5, imc, ome_zarr, zarr

if hdf5.available:
    controller.pm.register(hdf5, name="napari-dataset-hdf5")
if imc.available:
    controller.pm.register(imc, name="napari-dataset-imc")
if ome_zarr.available:
    controller.pm.register(ome_zarr, name="napari-dataset-ome-zarr")
if zarr.available:  # register after napari-dataset-ome-zarr!
    controller.pm.register(zarr, name="napari-dataset-zarr")

__all__ = [
    "controller",
    "DatasetController",
    "DatasetControllerException",
    "napari_get_reader",
]
