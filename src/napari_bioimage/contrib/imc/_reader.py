import os
from pathlib import Path
from typing import Union

from napari_bioimage.model import Image, ImageGroup

from .model import IMCAcquisitionLayer, IMCPanoramaLayer

try:
    import readimc
except ModuleNotFoundError:
    readimc = None

PathLike = Union[str, os.PathLike]


def read_imc(path: PathLike) -> Image:
    group = ImageGroup(name=Path(path).name)
    with readimc.MCDFile(path) as f:
        for slide in f.slides:
            slide_group = ImageGroup(
                name=f"[S{slide.id:02d}] {slide.description}", parent=group
            )
            panoramas_group = ImageGroup(name="Panoramas", parent=slide_group)
            for panorama in slide.panoramas:
                panorama_image = Image(
                    name=f"[P{panorama.id:02d}] {panorama.description}",
                    parent=panoramas_group,
                )
                panorama_layer = IMCPanoramaLayer(
                    name=f"{group.name} [S{slide.id:02d} P{panorama.id:02d}]",
                    image=panorama_image,
                    mcd_file=str(path),
                    slide_id=slide.id,
                    panorama_id=panorama.id,
                )
                panorama_image.layers.append(panorama_layer)
                panoramas_group.children.append(panorama_image)
            slide_group.children.append(panoramas_group)
            acquisitions_group = ImageGroup(name="Acquisitions", parent=slide_group)
            for acquisition in slide.acquisitions:
                acquisition_image = Image(
                    name=f"[A{acquisition.id:02d}] {acquisition.description}",
                    parent=acquisitions_group,
                )
                for channel_index, (channel_name, channel_label) in enumerate(
                    zip(acquisition.channel_names, acquisition.channel_labels)
                ):
                    acquisition_layer = IMCAcquisitionLayer(
                        name=(
                            f"{group.name} ["
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
            slide_group.children.append(acquisitions_group)
            group.children.append(slide_group)
    return group
