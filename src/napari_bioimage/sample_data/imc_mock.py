from pathlib import Path
from shutil import copyfileobj
from tempfile import TemporaryDirectory
from urllib.parse import urlparse
from urllib.request import urlopen

from napari.viewer import current_viewer

from .._controller import controller

image_url = (
    "https://github.com/BodenmillerGroup/TestData/raw/main/datasets"
    "/210308_ImcTestData/raw/20210305_NE_mockData1/20210305_NE_mockData1.mcd"
)
temp_dir = TemporaryDirectory()


def make_sample_data():
    mcd_file_name = Path(urlparse(image_url).path).name
    mcd_file = Path(temp_dir.name) / mcd_file_name
    if not mcd_file.exists():
        with mcd_file.open("wb") as fdst:
            with urlopen(image_url) as fsrc:
                copyfileobj(fsrc, fdst)
    controller.read(mcd_file)
    viewer = controller.viewer or current_viewer()
    assert viewer is not None
    if controller.viewer != viewer:
        controller.register_viewer(viewer)
    viewer.window.add_plugin_dock_widget("napari-bioimage", widget_name="images")
    viewer.window.add_plugin_dock_widget("napari-bioimage", widget_name="layers")
    return []
