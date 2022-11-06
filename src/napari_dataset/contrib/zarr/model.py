from napari_dataset.model import Layer


class ZarrLayer(Layer):
    zarr_file: str
    zarr_path: str
