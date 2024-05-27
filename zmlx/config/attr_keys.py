"""
用于管理Seepage的动态属性
"""
import warnings

from zml import Seepage


class DynKeys:
    """
    用于管理Seepage的动态属性
    """

    def __init__(self, model=None, ty=None):
        """
        初始化.
        """
        if isinstance(model, Seepage):
            self.model = model
        else:
            self.model = Seepage()

        if isinstance(ty, str):
            self.ty = ty
        else:
            self.ty = ''

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

    def get_keys(self):
        return self.model.get_keys()


def model_keys(m=None):
    """
    注册并返回用于model的键值 (与 model.reg_model_key 保持一致)
    """
    return DynKeys(m, 'm_')


def cell_keys(m=None):
    """
    注册并返回用于cell的键值 (与 model.reg_cell_key 保持一致)
    """
    return DynKeys(m, 'n_')


def face_keys(m=None):
    """
    注册并返回用于face的键值(与 model.reg_face_key 保持一致)
    """
    return DynKeys(m, 'b_')


def flu_keys(m=None):
    """
    注册并返回用于flu的键值(与 model.reg_flu_key 保持一致)
    """
    return DynKeys(m, 'f_')


def frac_keys(m=None):
    """
    注册并返回用于Fracture的键值.
    注意：
        将裂缝的属性保存到seepage中并不是好的选项.
    """
    warnings.warn('please use zmlx.utility.AttrKeys instead', DeprecationWarning)
    return DynKeys(m, 'fr_')


def vtx_keys(m=None):
    """
    注册并返回用于Vertex的键值
    注意：
        将裂缝的属性保存到seepage中并不是好的选项.
    """
    warnings.warn('please use zmlx.utility.AttrKeys instead', DeprecationWarning)
    return DynKeys(m, 've_')


def test():
    ck = cell_keys()
    print(ck.x, ck.y, ck.z)
    print(ck.v)
    print(ck.s)
    print(ck.x, ck.y, ck.z)
    print(ck.v)
    print(ck.s)
    print(ck.get_keys())


if __name__ == '__main__':
    test()
