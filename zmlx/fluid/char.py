import warnings

from zml import Seepage


def create(den=1100, name=None):
    """
    Data from Maryelin.
        密度在1100到1800之间
    """
    vis = 1.0e30
    specific_heat = 1380
    return Seepage.FluDef(den=den, vis=vis, specific_heat=specific_heat, name=name)


def create_flu(*args, **kwargs):
    warnings.warn('use function <create> instead', DeprecationWarning, stacklevel=2)
    return create(*args, **kwargs)


if __name__ == '__main__':
    print(create())
