try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

from ._controller import BioImageController, BioImageControllerException, controller
from ._exceptions import BioImageException
from ._reader import napari_get_reader
from .contrib import imc, ome_zarr

if imc.available:
    controller.pm.register(imc, name="napari-bioimage-imc")
if ome_zarr.available:
    controller.pm.register(ome_zarr, name="napari-bioimage-ome-zarr")

__all__ = [
    "BioImageController",
    "BioImageControllerException",
    "controller",
    "BioImageException",
    "napari_get_reader",
]
