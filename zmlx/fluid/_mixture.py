from zmlx.exts import FluDef


def create_mixture(name: str, *components: FluDef, **others) -> FluDef:
    """
    创建混合物的定义
    """
    assert len(name) > 0, "The name of the mixture is empty."
    res = FluDef(name=name)

    for c in components:
        if isinstance(c, FluDef):
            assert len(c.name) > 0, "The name of the component is not empty."
            assert c.component_number == 0, "The component of the mixture must be a single component."
            res.add_component(c)

    for k, v in others.items():
        if isinstance(v, FluDef):
            assert isinstance(k, str), "The component of the mixture must be a string."
            assert isinstance(v, FluDef), "The component of the mixture must be a FluDef."
            assert v.component_number == 0, "The component of the mixture must be a single component."
            res.add_component(name=k, flu=v)
    return res


def test():
    from zmlx.fluid import h2o, ch4
    gas = create_mixture('gas', ch4=ch4.create(), h2o=h2o.create())
    print(gas)


if __name__ == '__main__':
    test()
