import logging

DEFAULT_DRIVER = "OpenSCAD"


class Assembly:
    """Use multiple parts to build a product.

    Attributes
    ----------
    name
        The name given to the assembly.
    """

    def __init__(self, name: str):
        self.name = name

    def save(self):
        """Save the assembly to a JSON file."""
        logging.info(f"Saving assembly {self.name}")
        try:
            msg = "Assembly Save"
            raise NotImplementedError(msg)
        except Exception as error:
            logging.exception(error)

    def render(self, driver=None):
        """Render the Assembly to a 3D CAD format."""
        if driver is None:
            driver = DEFAULT_DRIVER
        driver = driver.lower().strip()
        logging.info(f"Rendering assembly {self.name} using driver={driver}")
        try:
            msg = "Assembly Render"
            raise NotImplementedError(msg)
        except Exception as error:
            logging.exception(error)
