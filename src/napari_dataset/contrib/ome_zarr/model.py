from typing import Optional

from napari_dataset.model import Dataset, Layer


class OMEZarrDataset(Dataset):
    ome_zarr_file: str


class OMEZarrImageLayer(Layer):
    channel_axis: Optional[int] = None
    channel_index: Optional[int] = None
    _ome_zarr_dataset: OMEZarrDataset


class OMEZarrLabelsLayer(Layer):
    label_name: str
    _ome_zarr_dataset: OMEZarrDataset
