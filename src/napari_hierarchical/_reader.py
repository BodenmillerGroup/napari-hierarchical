from napari.viewer import current_viewer

from ._controller import controller


def napari_get_reader(path):
    if isinstance(path, list):
        if len(path) != 1:
            return None
        path = path[0]
    if controller.can_read_group(path):
        return _reader_function
    return None


def _reader_function(path):
    controller.read_group(path)
    viewer = controller.viewer or current_viewer()
    assert viewer is not None
    if controller.viewer != viewer:
        controller.register_viewer(viewer)
    viewer.window.add_plugin_dock_widget("napari-hierarchical", widget_name="Groups")
    viewer.window.add_plugin_dock_widget("napari-hierarchical", widget_name="Arrays")
    return [(None,)]
