from zml import FractureNetwork, FracAlg, LinearExpr

network = FractureNetwork()

data = FractureNetwork.FractureData()
data.flu.clone(LinearExpr.create(1))

FracAlg.add_frac(network, p0=[-1, 0], p1=[1, 0], lave=2.0, data=data)
print(network)
for frac in network.fractures:
    assert isinstance(frac, FractureNetwork.FractureData)
    print(frac.flu)

data = FractureNetwork.FractureData()
data.flu.clone(LinearExpr.create(2))

FracAlg.add_frac(network, p0=[0, -1], p1=[0, 1], lave=2.0, data=data)
print(network)
for frac in network.fractures:
    assert isinstance(frac, FractureNetwork.FractureData)
    print(frac.flu)
