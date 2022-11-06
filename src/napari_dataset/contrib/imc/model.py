from napari_dataset.model import Dataset, Layer


class IMCDataset(Dataset):
    mcd_file: str


class IMCSlideDataset(Dataset):
    imc_dataset: IMCDataset
    slide_id: int


class IMCPanoramasDataset(Dataset):
    slide_dataset: IMCSlideDataset
    name: str = "Panoramas"


class IMCPanoramaDataset(Dataset):
    panoramas_dataset: IMCPanoramasDataset
    panorama_id: int


class IMCPanoramaLayer(Layer):
    panorama_dataset: IMCPanoramaDataset


class IMCAcquisitionsDataset(Dataset):
    slide_dataset: IMCSlideDataset
    name: str = "Acquisitions"


class IMCAcquisitionDataset(Dataset):
    acquisitions_dataset: IMCAcquisitionsDataset
    acquisition_id: int


class IMCAcquisitionLayer(Layer):
    acquisition_dataset: IMCAcquisitionDataset
    channel_index: int
