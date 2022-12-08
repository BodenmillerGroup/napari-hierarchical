import os
from pathlib import Path
from typing import Union

import numpy as np
from napari.layers import Image

from napari_hierarchical.model import Array, Group

from .model import IMCAcquisitionArray, IMCPanoramaArray

try:
    import dask.array as da
    from readimc import MCDFile
except ModuleNotFoundError:
    pass

PathLike = Union[str, os.PathLike]


def read_imc_group(path: PathLike) -> Group:
    group = Group(name=Path(path).name)
    with MCDFile(path) as f:
        for slide in f.slides:
            slide_group = Group(name=f"[S{slide.id:02d}] {slide.description}")
            panoramas_group = Group(name="Panoramas")
            for panorama in slide.panoramas:
                panorama_group = Group(
                    name=f"[P{panorama.id:02d}] {panorama.description}"
                )
                panorama_array = IMCPanoramaArray(
                    name=f"{group.name} [S{slide.id:02d} P{panorama.id:02d}]",
                    mcd_file=str(path),
                    slide_id=slide.id,
                    panorama_id=panorama.id,
                )
                panorama_group.arrays.append(panorama_array)
                panoramas_group.children.append(panorama_group)
            slide_group.children.append(panoramas_group)
            acquisitions_group = Group(name="Acquisitions")
            for acquisition in slide.acquisitions:
                acquisition_group = Group(
                    name=f"[A{acquisition.id:02d}] {acquisition.description}"
                )
                for channel_index, (channel_name, channel_label) in enumerate(
                    zip(acquisition.channel_names, acquisition.channel_labels)
                ):
                    acquisition_array = IMCAcquisitionArray(
                        name=f"{group.name} "
                        f"[S{slide.id:02d} A{acquisition.id:02d} C{channel_index:02d}]",
                        mcd_file=str(path),
                        slide_id=slide.id,
                        acquisition_id=acquisition.id,
                        channel_index=channel_index,
                    )
                    acquisition_array.flat_grouping_groups[
                        "Channel"
                    ] = f"[C{channel_index:02d}] {channel_name} {channel_label}"
                    acquisition_group.arrays.append(acquisition_array)
                acquisitions_group.children.append(acquisition_group)
            slide_group.children.append(acquisitions_group)
            group.children.append(slide_group)
    group.commit()
    return group


def load_imc_panorama_array(array: Array) -> None:
    if not isinstance(array, IMCPanoramaArray):
        raise TypeError(f"Not an IMC panorama array: {array}")
    with MCDFile(array.mcd_file) as f:
        slide = next(slide for slide in f.slides if slide.id == array.slide_id)
        panorama = next(
            panorama for panorama in slide.panoramas if panorama.id == array.panorama_id
        )
        data = da.from_array(f.read_panorama(panorama)[::-1, :])
        scale = (
            panorama.height_um / data.shape[0],
            panorama.width_um / data.shape[1],
        )
        translate = (
            panorama.points_um[0][1] - panorama.height_um,
            panorama.points_um[0][0],
        )
        rotate = -np.arctan2(
            panorama.points_um[1][1] - panorama.points_um[0][1],
            panorama.points_um[1][0] - panorama.points_um[0][0],
        )
    array.layer = Image(
        name=array.name, data=data, scale=scale, translate=translate, rotate=rotate
    )


def load_imc_acquisition_array(array: Array) -> None:
    if not isinstance(array, IMCAcquisitionArray):
        raise TypeError(f"Not an IMC acquisition array: {array}")
    with MCDFile(array.mcd_file) as f:
        slide = next(slide for slide in f.slides if slide.id == array.slide_id)
        acquisition = next(
            acquisition
            for acquisition in slide.acquisitions
            if acquisition.id == array.acquisition_id
        )
        data = da.from_array(
            f.read_acquisition(acquisition)[array.channel_index, ::-1, :]
        )
        scale = (
            acquisition.height_um / data.shape[0],
            acquisition.width_um / data.shape[1],
        )
        translate = (
            acquisition.roi_points_um[0][1] - acquisition.height_um,
            acquisition.roi_points_um[0][0],
        )
        rotate = -np.arctan2(
            acquisition.roi_points_um[1][1] - acquisition.roi_points_um[0][1],
            acquisition.roi_points_um[1][0] - acquisition.roi_points_um[0][0],
        )
    array.layer = Image(
        name=array.name, data=data, scale=scale, translate=translate, rotate=rotate
    )
