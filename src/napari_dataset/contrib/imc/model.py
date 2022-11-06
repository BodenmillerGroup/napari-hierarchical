from napari_dataset.model import Dataset, Layer


class IMCDataset(Dataset):
    mcd_file: str


class IMCSlideDataset(Dataset):
    slide_id: int
    _imc_dataset: IMCDataset


class IMCPanoramasDataset(Dataset):
    name: str = "Panoramas"
    _slide_dataset: IMCSlideDataset


class IMCPanoramaDataset(Dataset):
    panorama_id: int
    _panoramas_dataset: IMCPanoramasDataset


class IMCPanoramaLayer(Layer):
    _panorama_dataset: IMCPanoramaDataset


class IMCAcquisitionsDataset(Dataset):
    name: str = "Acquisitions"
    _slide_dataset: IMCSlideDataset


class IMCAcquisitionDataset(Dataset):
    acquisition_id: int
    _acquisitions_dataset: IMCAcquisitionsDataset


class IMCAcquisitionLayer(Layer):
    channel_index: int
    _acquisition_dataset: IMCAcquisitionDataset
