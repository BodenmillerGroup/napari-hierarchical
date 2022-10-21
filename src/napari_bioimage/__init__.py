try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

from ._controller import BioImageController, BioImageControllerException, controller
from ._exceptions import BioImageException
from ._reader import napari_get_reader
from .contrib import hdf5, imc, napari, ome_zarr, zarr

if hdf5.available:
    controller.pm.register(hdf5, name="napari-bioimage-hdf5")
if imc.available:
    controller.pm.register(imc, name="napari-bioimage-imc")
if napari.available:
    controller.pm.register(napari, name="napari-bioimage-napari")
if ome_zarr.available:
    controller.pm.register(ome_zarr, name="napari-bioimage-ome-zarr")
if zarr.available:  # register after napari-bioimage-ome-zarr!
    controller.pm.register(zarr, name="napari-bioimage-zarr")

__all__ = [
    "BioImageController",
    "BioImageControllerException",
    "controller",
    "BioImageException",
    "napari_get_reader",
]
