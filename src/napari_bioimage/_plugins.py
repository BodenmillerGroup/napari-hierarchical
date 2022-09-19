from pluggy import PluginManager

from . import hookspecs
from .contrib import imc, ome_zarr

pm = PluginManager("napari-bioimage")
pm.add_hookspecs(hookspecs)
pm.load_setuptools_entrypoints("napari-bioimage")
if imc.available:
    pm.register(imc, name="napari-bioimage-imc")
if ome_zarr.available:
    pm.register(ome_zarr, name="napari-bioimage-ome-zarr")
