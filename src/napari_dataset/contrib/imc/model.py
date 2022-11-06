from napari_dataset.model import Layer


class IMCPanoramaLayer(Layer):
    mcd_file: str
    slide_id: int
    panorama_id: int


class IMCAcquisitionLayer(Layer):
    mcd_file: str
    slide_id: int
    acquisition_id: int
    channel_index: int
