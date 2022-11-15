from contextlib import contextmanager

from napari.viewer import current_viewer
from s3fs import S3FileSystem

from .._controller import controller

s3_endpoint_url = "https://uk1s3.embassy.ebi.ac.uk"
url = "s3://idr/zarr/v0.4/idr0052A/5514375.zarr"


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
        controller.read_group(url)
    viewer = controller.viewer or current_viewer()
    assert viewer is not None
    if controller.viewer != viewer:
        controller.register_viewer(viewer)
    viewer.window.add_plugin_dock_widget("napari-hierarchical", widget_name="Groups")
    viewer.window.add_plugin_dock_widget("napari-hierarchical", widget_name="Arrays")
    return []
