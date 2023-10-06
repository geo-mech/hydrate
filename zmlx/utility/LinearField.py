


class LinearField:
    """
    线性的温度场或者压力场。用于辅助建模;
    """

    def __init__(self, x0=0, y0=0, z0=0, v0=0, dx=0, dy=0, dz=0):
        self.x0 = x0
        self.y0 = y0
        self.z0 = z0
        self.v0 = v0
        self.dx = dx
        self.dy = dy
        self.dz = dz

    def __call__(self, x, y, z):
        return self.v0 + (x - self.x0) * self.dx + (y - self.y0) * self.dy + (z - self.z0) * self.dz
