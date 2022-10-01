from .._controller import controller

image_url = "https://uk1s3.embassy.ebi.ac.uk/idr/zarr/v0.4/idr0052A/5514375.zarr"


def make_sample_data():
    controller.read_image(image_url)
    return []
