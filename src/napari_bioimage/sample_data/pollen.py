from pathlib import Path
from shutil import copyfileobj
from tempfile import TemporaryDirectory
from urllib.parse import urlparse
from urllib.request import urlopen

from napari.viewer import current_viewer

from .._controller import controller

image_url = (
    "https://lmb.informatik.uni-freiburg.de"
    "/resources/opensource/imagej_plugins/samples/pollen.h5"
)
temp_dir = TemporaryDirectory()


def make_sample_data():
    h5_file_name = Path(urlparse(image_url).path).name
    h5_file = Path(temp_dir.name) / h5_file_name
    if not h5_file.exists():
        with h5_file.open("wb") as fdst:
            with urlopen(image_url) as fsrc:
                copyfileobj(fsrc, fdst)
    controller.read_image(h5_file)
    viewer = controller.viewer or current_viewer()
    assert viewer is not None
    if controller.viewer != viewer:
        controller.register_viewer(viewer)
    if controller.widget is None:
        _, widget = viewer.window.add_plugin_dock_widget("napari-bioimage")
        assert controller.widget == widget
    return []
