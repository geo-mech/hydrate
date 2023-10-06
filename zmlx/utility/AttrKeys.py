from zml import *


class AttrKeys:
    """
    用以管理动态的属性
    """
    def __init__(self, model, ty):
        assert isinstance(model, Seepage)
        assert isinstance(ty, str)
        self.model = model
        self.ty = ty

    def __getattr__(self, item):
        assert isinstance(item, str)
        return self.model.reg_key(self.ty, item)

    def __getitem__(self, item):
        assert isinstance(item, str)
        return self.model.reg_key(self.ty, item)


def model_keys(m):
    """
    注册并返回用于model的键值 (与 model.reg_model_key 保持一致)
    """
    return AttrKeys(m, 'm_')


def cell_keys(m):
    """
    注册并返回用于cell的键值 (与 model.reg_cell_key 保持一致)
    """
    return AttrKeys(m, 'n_')


def face_keys(m):
    """
    注册并返回用于face的键值(与 model.reg_face_key 保持一致)
    """
    return AttrKeys(m, 'b_')


def flu_keys(m):
    """
    注册并返回用于flu的键值(与 model.reg_flu_key 保持一致)
    """
    return AttrKeys(m, 'f_')


def frac_keys(m):
    """
    注册并返回用于frac的键值
    """
    return AttrKeys(m, 'fr_')


def test():
    m = Seepage()
    ck = cell_keys(m)
    print(ck.x, ck.y, ck.z)
    print(ck.v)
    print(ck.s)
    print(ck.x, ck.y, ck.z)
    print(ck.v)
    print(ck.s)


if __name__ == '__main__':
    test()

