from napari_hierarchical.model import Array


class ZarrArray(Array):
    zarr_file: str
    zarr_path: str
