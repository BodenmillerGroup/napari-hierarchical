import os
from pathlib import Path
from typing import Union

from napari.layers import Layer as NapariLayer
from napari.viewer import Viewer
from readimc import MCDFile

from napari_bioimage.model import Image, ImageGroup, Layer

from ._exceptions import BioImageIMCException
from .model import (
    IMCAcquisitionImage,
    IMCAcquisitionLayer,
    IMCImage,
    IMCPanoramaImage,
    IMCPanoramaLayer,
    IMCSlideImage,
)

PathLike = Union[str, os.PathLike]


def read_imc_image(path: PathLike) -> Image:
    try:
        image = IMCImage(name=Path(path).name, mcd_file=str(path))
        with MCDFile(path) as f:
            for slide in f.slides:
                slide_image = IMCSlideImage(
                    name=f"[S{slide.id:02d}] {slide.description}",
                    parent=image,
                    mcd_file=str(path),
                    slide_id=slide.id,
                )
                panoramas_group = ImageGroup(name="Panoramas", parent=slide_image)
                for panorama in slide.panoramas:
                    panorama_image = IMCPanoramaImage(
                        name=f"[P{panorama.id:02d}] {panorama.description}",
                        parent=panoramas_group,
                        mcd_file=str(path),
                        slide_id=slide.id,
                        panorama_id=panorama.id,
                    )
                    panorama_layer = IMCPanoramaLayer(
                        name=f"{image.name} [S{slide.id:02d} P{panorama.id:02d}]",
                        image=panorama_image,
                        mcd_file=str(path),
                        slide_id=slide.id,
                        panorama_id=panorama.id,
                    )
                    panorama_image.layers.append(panorama_layer)
                    panoramas_group.children.append(panorama_image)
                slide_image.children.append(panoramas_group)
                acquisitions_group = ImageGroup(name="Acquisitions", parent=slide_image)
                for acquisition in slide.acquisitions:
                    acquisition_image = IMCAcquisitionImage(
                        name=f"[A{acquisition.id:02d}] {acquisition.description}",
                        parent=acquisitions_group,
                        mcd_file=str(path),
                        slide_id=slide.id,
                        acquisition_id=acquisition.id,
                    )
                    for channel_index, (channel_name, channel_label) in enumerate(
                        zip(acquisition.channel_names, acquisition.channel_labels)
                    ):
                        acquisition_layer = IMCAcquisitionLayer(
                            name=(
                                f"{image.name} ["
                                f"S{slide.id:02d} "
                                f"A{acquisition.id:02d} "
                                f"C{channel_index:02d}]"
                            ),
                            image=acquisition_image,
                            mcd_file=str(path),
                            slide_id=slide.id,
                            acquisition_id=acquisition.id,
                            channel_index=channel_index,
                        )
                        acquisition_layer.metadata[
                            "Channel"
                        ] = f"[C{channel_index:02d}] {channel_name} {channel_label}"
                        acquisition_image.layers.append(acquisition_layer)
                    acquisitions_group.children.append(acquisition_image)
                slide_image.children.append(acquisitions_group)
                image.children.append(slide_image)
        return image
    except Exception as e:
        raise BioImageIMCException(e)


def load_imc_layer(layer: Layer, viewer: Viewer) -> NapariLayer:
    if isinstance(layer, IMCPanoramaLayer):
        with MCDFile(layer.mcd_file) as f:
            slide = next(slide for slide in f.slides if slide.id == layer.slide_id)
            panorama = next(
                panorama
                for panorama in slide.panoramas
                if panorama.id == layer.panorama_id
            )
            data = f.read_panorama(panorama)
        return viewer.add_image(
            data=data, name=layer.name, metadata={"napari_bioimage_layer": layer}
        )  # TODO scale, translation, rotation
    if isinstance(layer, IMCAcquisitionLayer):
        with MCDFile(layer.mcd_file) as f:
            slide = next(slide for slide in f.slides if slide.id == layer.slide_id)
            acquisition = next(
                acquisition
                for acquisition in slide.acquisitions
                if acquisition.id == layer.acquisition_id
            )
            data = f.read_acquisition(acquisition)[layer.channel_index]
        # TODO read acquisition from TXT if reading from MCD failes
        return viewer.add_image(
            data=data, name=layer.name, metadata={"napari_bioimage_layer": layer}
        )  # TODO scale, rotation, translation
    raise BioImageIMCException(f"Unsupported layer type: {type(layer)}")
