from napari_bioimage.model import Image, ImageGroup, Layer


class IMCImage(ImageGroup):
    mcd_file: str


class IMCSlideImage(ImageGroup):
    mcd_file: str
    slide_id: int


class IMCPanoramaImage(Image):
    mcd_file: str
    slide_id: int
    panorama_id: int


class IMCAcquisitionImage(Image):
    mcd_file: str
    slide_id: int
    acquisition_id: int


class IMCLayer(Layer):
    pass


class IMCPanoramaLayer(IMCLayer):
    mcd_file: str
    slide_id: int
    panorama_id: int


class IMCAcquisitionLayer(IMCLayer):
    mcd_file: str
    slide_id: int
    acquisition_id: int
    channel_index: int
