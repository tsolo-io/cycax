from cycax.cycad import Print3D


class SimpleCube(Print3D):
    def __init__(self):
        super().__init__(
            part_no="simple_cube",
            x_size=20,  # 20mm width
            y_size=20,  # 20mm depth
            z_size=20,  # 20mm height
        )


# Create and render the part
cube = SimpleCube()
cube.save()
cube.render()
