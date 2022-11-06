from typing import Optional

from napari_dataset.model import Dataset, Layer


class OMEZarrDataset(Dataset):
    ome_zarr_file: str


class OMEZarrImageLayer(Layer):
    ome_zarr_dataset: OMEZarrDataset
    channel_axis: Optional[int] = None
    channel_index: Optional[int] = None


class OMEZarrLabelsLayer(Layer):
    ome_zarr_dataset: OMEZarrDataset
    label_name: str
