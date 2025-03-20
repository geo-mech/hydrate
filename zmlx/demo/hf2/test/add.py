from zml import FractureNetwork, LinearExpr, Seepage
from zmlx.demo.hf2.alg import update_topology


def main():
    network = FractureNetwork()

    data = FractureNetwork.FractureData()
    data.flu_expr.clone(LinearExpr.create(1))

    network.add_fracture(pos=[-1, 0, 1, 0], lave=2.0, data=data)
    print(network)
    for f in network.fractures:
        assert isinstance(f, FractureNetwork.FractureData)
        print(f.flu_expr)

    data.flu_expr.clone(LinearExpr.create(2))

    network.add_fracture(pos=[0, -1, 0, 1], lave=2.0, data=data)
    print(network)
    for f in network.fractures:
        assert isinstance(f, FractureNetwork.FractureData)
        print(f.flu_expr)

    model = Seepage()
    update_topology(model, network)
    print(model)


if __name__ == '__main__':
    main()
