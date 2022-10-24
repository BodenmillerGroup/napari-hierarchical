from napari.layers import Image as NapariImageLayer
from napari.layers import Layer as NapariLayer

from napari_bioimage.model import Layer

try:
    import readimc
except ModuleNotFoundError:
    readimc = None


class IMCLayer(Layer):
    mcd_file: str
    slide_id: int


class IMCPanoramaLayer(IMCLayer):
    panorama_id: int

    def load(self) -> NapariLayer:
        with readimc.MCDFile(self.mcd_file) as f:
            slide = next(slide for slide in f.slides if slide.id == self.slide_id)
            panorama = next(
                panorama
                for panorama in slide.panoramas
                if panorama.id == self.panorama_id
            )
            data = f.read_panorama(panorama)
        napari_layer = NapariImageLayer(
            name=self.name, data=data
        )  # TODO scale/translation/rotation
        return napari_layer


class IMCAcquisitionLayer(IMCLayer):
    acquisition_id: int
    channel_index: int

    def load(self) -> NapariLayer:
        with readimc.MCDFile(self.mcd_file) as f:
            slide = next(slide for slide in f.slides if slide.id == self.slide_id)
            acquisition = next(
                acquisition
                for acquisition in slide.acquisitions
                if acquisition.id == self.acquisition_id
            )
            data = f.read_acquisition(acquisition)[self.channel_index]
        # TODO read acquisition from TXT if reading from MCD fails
        napari_layer = NapariImageLayer(
            name=self.name, data=data
        )  # TODO scale/translation/rotation
        return napari_layer
