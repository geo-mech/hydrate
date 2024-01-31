"""
用于管理Seepage的动态属性
"""
from zml import Seepage
import warnings


class DynKeys:
    """
    用于管理Seepage的动态属性
    """

    def __init__(self, model, ty):
        """
        初始化.
        """
        assert isinstance(model, Seepage)
        assert isinstance(ty, str)
        self.model = model
        self.ty = ty

    def reg_key(self, item):
        """
        注册并且返回属性id
        """
        assert isinstance(item, str)
        return self.model.reg_key(self.ty, item)

    def reg_keys(self, *keys):
        """
        注册多个key，并且不返回任何的id (仅仅注册)
        """
        for key in keys:
            self.reg_key(key)

    def __getattr__(self, item):
        return self.reg_key(item)

    def __getitem__(self, item):
        return self.reg_key(item)


def model_keys(m):
    """
    注册并返回用于model的键值 (与 model.reg_model_key 保持一致)
    """
    return DynKeys(m, 'm_')


def cell_keys(m):
    """
    注册并返回用于cell的键值 (与 model.reg_cell_key 保持一致)
    """
    return DynKeys(m, 'n_')


def face_keys(m):
    """
    注册并返回用于face的键值(与 model.reg_face_key 保持一致)
    """
    return DynKeys(m, 'b_')


def flu_keys(m):
    """
    注册并返回用于flu的键值(与 model.reg_flu_key 保持一致)
    """
    return DynKeys(m, 'f_')


def frac_keys(m):
    """
    注册并返回用于Fracture的键值.
    注意：
        将裂缝的属性保存到seepage中并不是好的选项.
    """
    warnings.warn('please use zmlx.utility.AttrKeys instead', DeprecationWarning)
    return DynKeys(m, 'fr_')


def vtx_keys(m):
    """
    注册并返回用于Vertex的键值
    注意：
        将裂缝的属性保存到seepage中并不是好的选项.
    """
    warnings.warn('please use zmlx.utility.AttrKeys instead', DeprecationWarning)
    return DynKeys(m, 've_')


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
