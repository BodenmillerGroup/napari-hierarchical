from typing import Optional

import numpy as np
from napari.layers import Image as NapariImageLayer
from napari.layers import Labels as NapariLabelsLayer
from napari.layers import Layer as NapariLayer

from napari_bioimage.model import Layer

try:
    import ome_zarr
    from ome_zarr.io import ZarrLocation
    from ome_zarr.reader import Multiscales
    from ome_zarr.reader import Node as ZarrNode
    from ome_zarr.reader import Reader as ZarrReader
except ModuleNotFoundError:
    ome_zarr = None


class OMEZarrLayer(Layer):
    ome_zarr_file: str


class OMEZarrImageLayer(OMEZarrLayer):
    channel_axis: Optional[int] = None
    channel_index: Optional[int] = None

    def load(self) -> NapariLayer:
        zarr_location = ZarrLocation(str(self.ome_zarr_file))
        zarr_reader = ZarrReader(zarr_location)
        zarr_node = ZarrNode(zarr_location, zarr_reader)
        multiscales = Multiscales(zarr_node)
        data = [
            multiscales.array(resolution, "") for resolution in multiscales.datasets
        ]  # TODO version
        if self.channel_axis is not None and self.channel_index is not None:
            data = [
                np.take(a, self.channel_index, axis=self.channel_axis) for a in data
            ]
        napari_layer = NapariImageLayer(name=self.name, data=data, multiscale=True)
        return napari_layer

    def save(self) -> None:
        raise NotImplementedError()  # TODO


class OMEZarrLabelsLayer(OMEZarrLayer):
    label_name: str

    def load(self) -> NapariLayer:
        zarr_location = ZarrLocation(str(self.ome_zarr_file))
        labels_zarr_location = ZarrLocation(zarr_location.subpath("labels"))
        label_zarr_location = ZarrLocation(
            labels_zarr_location.subpath(self.label_name)
        )
        label_zarr_reader = ZarrReader(label_zarr_location)
        label_zarr_node = ZarrNode(label_zarr_location, label_zarr_reader)
        label_multiscales = Multiscales(label_zarr_node)
        data = [
            label_multiscales.array(resolution, "")
            for resolution in label_multiscales.datasets
        ]  # TODO version
        napari_layer = NapariLabelsLayer(name=self.name, data=data, multiscale=True)
        return napari_layer

    def save(self) -> None:
        raise NotImplementedError()  # TODO
