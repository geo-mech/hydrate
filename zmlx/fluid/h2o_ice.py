import warnings

from zml import Seepage


def create(name=None):
    """
    冰的密度：https://zhidao.baidu.com/question/327692583825967245.html
    https://baike.baidu.com/item/%E5%86%B0/84742

    冰在0℃下密度为0.917 g/cm³。
    在常压环境下，冰的熔点为0℃。0℃水冻结成冰时，体积会增大约1/9（水体积最小时为4℃）。据观测，封闭条件下水冻结时，体积增加所产生的压强可达2500大气压。


    冰的比热：
    https://zhidao.baidu.com/question/919092470639544179.html

    冰的比热容是：2100J/(KG.℃)
    比热容的单位：J/(kg•°C)
    """
    den = 917.0
    specific_heat = 2100.0
    return Seepage.FluDef(den=den,
                          vis=1.0e30,
                          specific_heat=specific_heat, name=name)


def create_flu(*args, **kwargs):
    warnings.warn('use function <create> instead', DeprecationWarning,
                  stacklevel=2)
    return create(*args, **kwargs)


if __name__ == '__main__':
    flu = create()
    print(flu)
