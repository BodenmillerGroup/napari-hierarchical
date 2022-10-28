from typing import Optional, Tuple

from napari_dataset.model import Dataset, Layer


class ZarrDataset(Dataset):
    zarr_file: str

    @staticmethod
    def get_root(dataset: Dataset) -> Tuple[Optional["ZarrDataset"], str]:
        dataset_names = []
        while dataset.parent is not None or (
            dataset is not None and not isinstance(dataset, ZarrDataset)
        ):
            dataset_names.append(dataset.name)
            dataset = dataset.parent
        return dataset, "/".join(reversed(dataset_names))


class ZarrLayer(Layer):
    root_zarr_dataset: ZarrDataset
