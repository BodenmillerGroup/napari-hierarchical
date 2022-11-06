from napari_dataset.model import Dataset, Layer


class ZarrDataset(Dataset):
    zarr_file: str


class ZarrLayer(Layer):
    _root_zarr_dataset: ZarrDataset
