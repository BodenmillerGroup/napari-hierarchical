import os
from pathlib import Path
from typing import Union

from napari_dataset.model import Dataset

from .model import IMCAcquisitionLayer, IMCPanoramaLayer

try:
    import readimc
except ModuleNotFoundError:
    readimc = None

PathLike = Union[str, os.PathLike]


def read_imc(path: PathLike) -> Dataset:
    dataset = Dataset(name=Path(path).name)
    with readimc.MCDFile(path) as f:
        for slide in f.slides:
            slide_dataset = Dataset(
                name=f"[S{slide.id:02d}] {slide.description}", parent=dataset
            )
            panoramas_dataset = Dataset(name="Panoramas", parent=slide_dataset)
            for panorama in slide.panoramas:
                panorama_dataset = Dataset(
                    name=f"[P{panorama.id:02d}] {panorama.description}",
                    parent=panoramas_dataset,
                )
                panorama_layer = IMCPanoramaLayer(
                    name=f"{dataset.name} [S{slide.id:02d} P{panorama.id:02d}]",
                    dataset=panorama_dataset,
                    mcd_file=str(path),
                    slide_id=slide.id,
                    panorama_id=panorama.id,
                )
                panorama_dataset.layers.append(panorama_layer)
                panoramas_dataset.children.append(panorama_dataset)
            slide_dataset.children.append(panoramas_dataset)
            acquisitions_dataset = Dataset(name="Acquisitions", parent=slide_dataset)
            for acquisition in slide.acquisitions:
                acquisition_dataset = Dataset(
                    name=f"[A{acquisition.id:02d}] {acquisition.description}",
                    parent=acquisitions_dataset,
                )
                for channel_index, (channel_name, channel_label) in enumerate(
                    zip(acquisition.channel_names, acquisition.channel_labels)
                ):
                    acquisition_layer = IMCAcquisitionLayer(
                        name=(
                            f"{dataset.name} ["
                            f"S{slide.id:02d} "
                            f"A{acquisition.id:02d} "
                            f"C{channel_index:02d}]"
                        ),
                        dataset=acquisition_dataset,
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
            dataset.children.append(slide_dataset)
    return dataset
