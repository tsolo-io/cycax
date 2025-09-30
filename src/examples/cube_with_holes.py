from cycax.cycad import Print3D


class CubeWithHoles(Print3D):
    def __init__(self):
        super().__init__(part_no="cube_with_holes", x_size=30, y_size=30, z_size=20)

    def definition(self):
        """Define the part features."""
        # Add a 10mm deep hole to front face
        self.front.hole(
            pos=(15, 10),  # Center of the face
            diameter=5,  # 5mm diameter
            depth=10,  # 10mm deep
        )

        # Add holes through the top face
        for x in [10, 20]:
            for y in [10, 20]:
                self.top.hole(pos=(x, y), diameter=3)


# Create and render
part = CubeWithHoles()
part.save()
part.render()
