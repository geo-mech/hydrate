from zml import *


def show(network: FractureNetwork):
    print(network)
    for f in network.fractures:
        assert isinstance(f, FractureNetwork.Fracture)
        print(f.center, f.ds)

def main():
    network = FractureNetwork()
    network.add_fracture(first=[0, 0], second=[10, 0], lave=0.5)
    for f in network.fractures:
        assert isinstance(f, FractureNetwork.Fracture)
        x, y = f.center
        f.ds = x
    show(network)

    for f in network.fractures:
        assert isinstance(f, FractureNetwork.Fracture)
        x, y = f.center
        if x < 5:
            f.set_attr(index=0, value=1)

    sub = network.get_sub_network(fa_key=0)
    show(sub)

    for f in sub.fractures:
        f.ds = -1

    show(sub)

    network.copy_fracture_from_sub_network(fa_key=0, sub=sub)
    show(network)


if __name__ == '__main__':
    main()


