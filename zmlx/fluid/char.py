import warnings

from zml import TherFlowConfig


def create(den=1100):
    """
    Data from Maryelin.
        密度在1100到1800之间
    """
    vis = 1.0e30
    specific_heat = 1380
    return TherFlowConfig.FluProperty(den=den, vis=vis, specific_heat=specific_heat)


def create_flu(*args, **kwargs):
    warnings.warn('use function <create> instead', DeprecationWarning)
    return create(*args, **kwargs)


if __name__ == '__main__':
    print(create_flu())
