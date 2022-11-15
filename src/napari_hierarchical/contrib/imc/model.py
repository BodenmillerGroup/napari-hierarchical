from napari_hierarchical.model import Array


class IMCArray(Array):
    mcd_file: str
    slide_id: int


class IMCPanoramaArray(IMCArray):
    panorama_id: int


class IMCAcquisitionArray(IMCArray):
    acquisition_id: int
    channel_index: int
