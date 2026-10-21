"""IP 信息查询工具.

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""


from zmlx.system import warn
from zmlx.algs.sys import get_ipinfo, get_city

warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)


def _test():
    """
    测试
    """
    info = get_ipinfo()
    ip = info.get('ip')
    location = info.get('loc')
    city = info.get('city')
    region = info.get('region')
    country = info.get('country')

    print(
        f"IP: {ip}, Location: {location}, City: {city}, Region: {region}, Country: {country}")


if __name__ == '__main__':
    print(get_city())
