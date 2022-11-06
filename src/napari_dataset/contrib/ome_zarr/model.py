from typing import Optional

from napari_dataset.model import Layer


class OMEZarrImageLayer(Layer):
    ome_zarr_file: str
    channel_axis: Optional[int] = None
    channel_index: Optional[int] = None


class OMEZarrLabelsLayer(Layer):
    ome_zarr_file: str
    label_name: str
