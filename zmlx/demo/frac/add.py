from zml import FractureNetwork, FracAlg

network = FractureNetwork()

FracAlg.add_frac(network, p0=[-1, 0], p1=[1, 0], lave=2.0)
print(network)

FracAlg.add_frac(network, p0=[0, -1], p1=[0, 1], lave=2.0)
print(network)
