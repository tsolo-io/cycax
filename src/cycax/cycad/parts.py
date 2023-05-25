import logging

DEFAULT_PART_DRIVER = "OpenSCAD"

class BasePart:  # Consider making this an ABC if it will help.
    colour = "grey"

    def __init__(self, name: str):
        self.name = name

    def save(self):
        """Save the assembly to a JSON file."""
        logging.info(f"Saving assembly {self.name}")
        try:
            raise NotImplementedError("Part Save")
        except Exception as error:
            logging.exception(error)

    def render(self, driver=None):
        """Render the Assembly to a 3D CAD format."""
        if driver is None:
            driver = DEFAULT_PART_DRIVER
        driver = driver.lower().strip()
        logging.info(f"Rendering assembly {self.name} using driver={driver}")
        try:
            raise NotImplementedError("Part Render")
        except Exception as error:
            logging.exception(error)

class Part3dPrint(BasePart):
    fillamet_type = "PLA"

    def filamet(self, filament_type="PLA", colour: str = ""):
        """Set the type and properties of the 3D printing filament.

        Some of these settings are used for the rendering other settings are stored to be
        used my manufacturing processes.
        """
        self.fillamet_type = fillamet_type
        if colour:
            self.colour = colour

class PartSheet(BasePart):
    material_type = "Aluminium"
    form_process = "Laser"

    def metrial(self, material_type="Aluminium", colour: str = ""):
        """Set the type and properties of the sheet.

        Some of these settings are used for the rendering other settings are stored to be
        used my manufacturing processes. Typicaly Aliminium, Galvanised steel, Perspex,
        and types of HDPE sheets are used. Sheets of wood to.
        """
        self.material_type = material_type
        if colour:
            self.colour = colour

    def form_processing(self, form_process=None):
        _fp = form_process.lower().strip()
        if _fp == 'laser':
            self.form_process = "Laser"
        elif _fp == 'mill':
            self.form_process = "Mill"
        else:
            raise ValueError(f"Do not know how to process {form_process}, we can Mill and Laser.")
