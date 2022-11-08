import os
from pathlib import Path
from typing import Union

from napari.layers import Image as NapariImageLayer

from napari_dataset.model import Dataset, Layer

from .model import IMCAcquisitionLayer, IMCPanoramaLayer

try:
    import readimc
except ModuleNotFoundError:
    readimc = None

PathLike = Union[str, os.PathLike]


def read_imc_dataset(path: PathLike) -> Dataset:
    imc_dataset = Dataset(name=Path(path).name)
    with readimc.MCDFile(path) as f:
        for slide in f.slides:
            slide_dataset = Dataset(name=f"[S{slide.id:02d}] {slide.description}")
            panoramas_dataset = Dataset(name="Panoramas")
            for panorama in slide.panoramas:
                panorama_dataset = Dataset(
                    name=f"[P{panorama.id:02d}] {panorama.description}"
                )
                panorama_layer = IMCPanoramaLayer(
                    name=f"{imc_dataset.name} [S{slide.id:02d} P{panorama.id:02d}]",
                    mcd_file=str(path),
                    slide_id=slide.id,
                    panorama_id=panorama.id,
                )
                panorama_dataset.layers.append(panorama_layer)
                panoramas_dataset.children.append(panorama_dataset)
            slide_dataset.children.append(panoramas_dataset)
            acquisitions_dataset = Dataset(name="Acquisitions")
            for acquisition in slide.acquisitions:
                acquisition_dataset = Dataset(
                    name=f"[A{acquisition.id:02d}] {acquisition.description}"
                )
                for channel_index, (channel_name, channel_label) in enumerate(
                    zip(acquisition.channel_names, acquisition.channel_labels)
                ):
                    acquisition_layer = IMCAcquisitionLayer(
                        name=f"{imc_dataset.name} "
                        f"[S{slide.id:02d} A{acquisition.id:02d} C{channel_index:02d}]",
                        mcd_file=str(path),
                        slide_id=slide.id,
                        acquisition_id=acquisition.id,
                        channel_index=channel_index,
                    )
                    acquisition_layer.groups[
                        "Channel"
                    ] = f"[C{channel_index:02d}] {channel_name} {channel_label}"
                    acquisition_dataset.layers.append(acquisition_layer)
                acquisitions_dataset.children.append(acquisition_dataset)
            slide_dataset.children.append(acquisitions_dataset)
            imc_dataset.children.append(slide_dataset)
    return imc_dataset


def load_imc_panorama_layer(layer: Layer) -> None:
    if not isinstance(layer, IMCPanoramaLayer):
        raise TypeError(f"Not an IMC Panorama layer: {layer}")
    with readimc.MCDFile(layer.mcd_file) as f:
        slide = next(slide for slide in f.slides if slide.id == layer.slide_id)
        panorama = next(
            panorama for panorama in slide.panoramas if panorama.id == layer.panorama_id
        )
        data = f.read_panorama(panorama)
    layer.napari_layer = NapariImageLayer(name=layer.name, data=data)  # TODO transform


def load_imc_acquisition_layer(layer: Layer) -> None:
    if not isinstance(layer, IMCAcquisitionLayer):
        raise TypeError(f"Not an IMC Acquisition layer: {layer}")
    # TODO read acquisition from TXT if reading from MCD fails
    with readimc.MCDFile(layer.mcd_file) as f:
        slide = next(slide for slide in f.slides if slide.id == layer.slide_id)
        acquisition = next(
            acquisition
            for acquisition in slide.acquisitions
            if acquisition.id == layer.acquisition_id
        )
        data = f.read_acquisition(acquisition)[layer.channel_index]
    layer.napari_layer = NapariImageLayer(name=layer.name, data=data)  # TODO transform
