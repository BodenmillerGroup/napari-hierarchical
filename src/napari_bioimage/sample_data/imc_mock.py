from .._controller import controller


def make_sample_data():
    controller.read_image(
        "https://github.com/BodenmillerGroup/TestData/raw/main/datasets/"
        "210308_ImcTestData/raw/20210305_NE_mockData1/20210305_NE_mockData1.mcd"
    )
    return []
