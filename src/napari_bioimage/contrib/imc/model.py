from napari_bioimage.model import Layer


class IMCLayer(Layer):
    mcd_file: str
    slide_id: int


class IMCPanoramaLayer(IMCLayer):
    panorama_id: int


class IMCAcquisitionLayer(IMCLayer):
    acquisition_id: int
    channel_index: int
