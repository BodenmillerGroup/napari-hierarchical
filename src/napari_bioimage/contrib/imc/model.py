from napari_bioimage.model import Image, ImageGroup, Layer


class IMCImage(ImageGroup):
    path: str


class IMCSlideImage(ImageGroup):
    slide_id: int

    @staticmethod
    def create(*args, **kwargs) -> "IMCSlideImage":
        slide_image = IMCSlideImage(*args, **kwargs)
        slide_image.children.append(ImageGroup(name="Panoramas", parent=slide_image))
        slide_image.children.append(ImageGroup(name="Acquisitions", parent=slide_image))
        return slide_image

    @property
    def panoramas_group(self) -> ImageGroup:
        return next(child for child in self.children if child.name == "Panoramas")

    @property
    def acquisitions_group(self) -> ImageGroup:
        return next(child for child in self.children if child.name == "Acquisitions")


class IMCPanoramaImage(Image):
    panorama_id: int


class IMCAcquisitionImage(Image):
    acquisition_id: int


class IMCLayer(Layer):
    pass


class IMCPanoramaLayer(IMCLayer):
    pass


class IMCAcquisitionLayer(IMCLayer):
    channel_index: int
