from napari.viewer import current_viewer

from .._controller import controller

image_url = "https://uk1s3.embassy.ebi.ac.uk/idr/zarr/v0.4/idr0052A/5514375.zarr"


def make_sample_data():
    controller.read_image(image_url)
    viewer = controller.viewer or current_viewer()
    assert viewer is not None
    if controller.viewer != viewer:
        controller.register_viewer(viewer)
    if controller.widget is None:
        _, widget = viewer.window.add_plugin_dock_widget("napari-bioimage")
        assert controller.widget == widget
    return []
