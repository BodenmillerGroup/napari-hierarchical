import os
from pathlib import Path
from typing import Union

from napari.layers import Image as NapariImageLayer
from napari.layers import Layer as NapariLayer

from napari_dataset.model import Dataset, Layer

from .model import (
    IMCAcquisitionDataset,
    IMCAcquisitionLayer,
    IMCAcquisitionsDataset,
    IMCDataset,
    IMCPanoramaDataset,
    IMCPanoramaLayer,
    IMCPanoramasDataset,
    IMCSlideDataset,
)

try:
    import readimc
except ModuleNotFoundError:
    readimc = None

PathLike = Union[str, os.PathLike]


def read_imc_dataset(path: PathLike) -> Dataset:
    imc_dataset = IMCDataset(name=Path(path).name, mcd_file=str(path))
    with readimc.MCDFile(path) as f:
        for slide in f.slides:
            slide_dataset = IMCSlideDataset(
                name=f"[S{slide.id:02d}] {slide.description}",
                imc_dataset=imc_dataset,
                slide_id=slide.id,
            )
            panoramas_dataset = IMCPanoramasDataset(slide_dataset=slide_dataset)
            for panorama in slide.panoramas:
                panorama_dataset = IMCPanoramaDataset(
                    name=f"[P{panorama.id:02d}] {panorama.description}",
                    panoramas_dataset=panoramas_dataset,
                    panorama_id=panorama.id,
                )
                panorama_layer = IMCPanoramaLayer(
                    name=f"{imc_dataset.name} [S{slide.id:02d} P{panorama.id:02d}]",
                    dataset=panorama_dataset,
                    panorama_dataset=panorama_dataset,
                )
                panorama_dataset.layers.append(panorama_layer)
                panoramas_dataset.children.append(panorama_dataset)
            slide_dataset.children.append(panoramas_dataset)
            acquisitions_dataset = IMCAcquisitionsDataset(slide_dataset=slide_dataset)
            for acquisition in slide.acquisitions:
                acquisition_dataset = IMCAcquisitionDataset(
                    name=f"[A{acquisition.id:02d}] {acquisition.description}",
                    acquisitions_dataset=acquisitions_dataset,
                    acquisition_id=acquisition.id,
                )
                for channel_index, (channel_name, channel_label) in enumerate(
                    zip(acquisition.channel_names, acquisition.channel_labels)
                ):
                    acquisition_layer = IMCAcquisitionLayer(
                        name=(
                            f"{imc_dataset.name} ["
                            f"S{slide.id:02d} "
                            f"A{acquisition.id:02d} "
                            f"C{channel_index:02d}]"
                        ),
                        dataset=acquisition_dataset,
                        acquisition_dataset=acquisition_dataset,
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


def load_imc_panorama_layer(layer: Layer) -> NapariLayer:
    if not isinstance(layer, IMCPanoramaLayer):
        raise TypeError(f"Not an IMC Panorama layer: {layer}")
    panorama_dataset = layer._panorama_dataset
    if layer.get_parent() != panorama_dataset:
        raise ValueError(f"Not part of original IMC dataset: {layer}")
    panoramas_dataset = panorama_dataset._panoramas_dataset
    if panorama_dataset.get_parent() != panoramas_dataset:
        raise ValueError(f"Not part of original IMC dataset: {layer}")
    slide_dataset = panoramas_dataset._slide_dataset
    if panoramas_dataset.get_parent() != slide_dataset:
        raise ValueError(f"Not part of original IMC dataset: {layer}")
    imc_dataset = slide_dataset._imc_dataset
    if (
        slide_dataset.get_parent() != imc_dataset
        or imc_dataset.get_parent() is not None
    ):
        raise ValueError(f"Not part of original IMC dataset: {layer}")
    with readimc.MCDFile(imc_dataset.mcd_file) as f:
        slide = next(slide for slide in f.slides if slide.id == slide_dataset.slide_id)
        panorama = next(
            panorama
            for panorama in slide.panoramas
            if panorama.id == panorama_dataset.panorama_id
        )
        data = f.read_panorama(panorama)
    return NapariImageLayer(name=layer.name, data=data)  # TODO transform


def load_imc_acquisition_layer(layer: Layer) -> NapariLayer:
    if not isinstance(layer, IMCAcquisitionLayer):
        raise TypeError(f"Not an IMC Acquisition layer: {layer}")
    acquisition_dataset = layer._acquisition_dataset
    if layer.get_parent() != acquisition_dataset:
        raise ValueError(f"Not part of original IMC dataset: {layer}")
    acquisitions_dataset = acquisition_dataset._acquisitions_dataset
    if acquisition_dataset.get_parent() != acquisitions_dataset:
        raise ValueError(f"Not part of original IMC dataset: {layer}")
    slide_dataset = acquisitions_dataset._slide_dataset
    if acquisitions_dataset.get_parent() != slide_dataset:
        raise ValueError(f"Not part of original IMC dataset: {layer}")
    imc_dataset = slide_dataset._imc_dataset
    if (
        slide_dataset.get_parent() != imc_dataset
        or imc_dataset.get_parent() is not None
    ):
        raise ValueError(f"Not part of original IMC dataset: {layer}")
    # TODO read acquisition from TXT if reading from MCD fails
    with readimc.MCDFile(imc_dataset.mcd_file) as f:
        slide = next(slide for slide in f.slides if slide.id == slide_dataset.slide_id)
        acquisition = next(
            acquisition
            for acquisition in slide.acquisitions
            if acquisition.id == acquisition_dataset.acquisition_id
        )
        data = f.read_acquisition(acquisition)[layer.channel_index]
    return NapariImageLayer(name=layer.name, data=data)  # TODO transform
