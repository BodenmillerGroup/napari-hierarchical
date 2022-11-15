from pathlib import Path
from shutil import copyfileobj
from tempfile import TemporaryDirectory
from urllib.parse import urlparse
from urllib.request import urlopen

from napari.viewer import current_viewer

from .._controller import controller

url = (
    "https://lmb.informatik.uni-freiburg.de"
    "/resources/opensource/imagej_plugins/samples/pollen.h5"
)
temp_dir = TemporaryDirectory()


def make_sample_data():
    hdf5_file_name = Path(urlparse(url).path).name
    hdf5_file = Path(temp_dir.name) / hdf5_file_name
    if not hdf5_file.exists():
        with hdf5_file.open("wb") as fdst:
            with urlopen(url) as fsrc:
                copyfileobj(fsrc, fdst)
    controller.read_group(hdf5_file)
    viewer = controller.viewer or current_viewer()
    assert viewer is not None
    if controller.viewer != viewer:
        controller.register_viewer(viewer)
    viewer.window.add_plugin_dock_widget("napari-hierarchical", widget_name="Groups")
    viewer.window.add_plugin_dock_widget("napari-hierarchical", widget_name="Arrays")
    return []
