import napari

from napari_bioimage.widgets import QImagesWidget, QLayersWidget


def main():
    viewer = napari.Viewer()
    images_widget = QImagesWidget(viewer)
    layers_widget = QLayersWidget(viewer)
    viewer.window.add_dock_widget(images_widget, name="images", area="left")
    viewer.window.add_dock_widget(layers_widget, name="layers", area="left")
    # TODO move layer controls dock widget to bottom
    viewer.window._qt_viewer.dockLayerList.hide()
    napari.run()


if __name__ == "__main__":
    main()
