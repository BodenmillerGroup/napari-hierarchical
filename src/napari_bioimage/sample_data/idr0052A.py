from .._controller import controller


def make_sample_data():
    controller.read_image(
        "https://uk1s3.embassy.ebi.ac.uk/idr/zarr/v0.4/idr0052A/5514375.zarr"
    )
    return []
