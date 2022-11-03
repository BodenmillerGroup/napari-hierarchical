from contextlib import contextmanager

from napari.viewer import current_viewer
from s3fs import S3FileSystem

from .._controller import controller

s3_endpoint_url = "https://uk1s3.embassy.ebi.ac.uk"
dataset_url = "s3://idr/zarr/v0.4/idr0052A/5514375.zarr"


@contextmanager
def configure_s3() -> S3FileSystem:
    s3 = S3FileSystem.current()
    orig_s3_anon = s3.anon
    orig_s3_client_kwargs = s3.client_kwargs.copy()
    s3.anon = True
    s3.client_kwargs = {"endpoint_url": s3_endpoint_url}
    yield s3
    s3.anon = orig_s3_anon
    s3.client_kwargs = orig_s3_client_kwargs


def make_sample_data():
    with configure_s3():
        controller.read_dataset(dataset_url)
    viewer = controller.viewer or current_viewer()
    assert viewer is not None
    if controller.viewer != viewer:
        controller.register_viewer(viewer)
    viewer.window.add_plugin_dock_widget("napari-dataset", widget_name="datasets")
    viewer.window.add_plugin_dock_widget("napari-dataset", widget_name="layers")
    return []


def make_zarr_sample_data():
    from ..contrib import ome_zarr

    orig_ome_zarr_available = ome_zarr.available
    ome_zarr.available = False
    try:
        sample_data = make_sample_data()
    finally:
        ome_zarr.available = orig_ome_zarr_available
    return sample_data


def make_ome_zarr_sample_data():
    from ..contrib import zarr

    orig_zarr_available = zarr.available
    zarr.available = False
    try:
        sample_data = make_sample_data()
    finally:
        zarr.available = orig_zarr_available
    return sample_data
