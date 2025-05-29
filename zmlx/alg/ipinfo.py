import zmlx.alg.sys as warnings

from zmlx.alg.sys import get_ipinfo, get_city

warnings.warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
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
