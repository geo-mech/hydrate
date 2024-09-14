import http.client
import json


def get_ipinfo():
    """
    返回当前主机的IP信息
    """
    conn = http.client.HTTPSConnection("ipinfo.io")
    conn.request("GET", "/json")
    response = conn.getresponse()
    data = response.read().decode()
    conn.close()
    info = json.loads(data)
    return info


def get_city():
    """
    获得当前主机的位置(具体到城市)
    """
    info = get_ipinfo()
    return info.get('city', 'error') + ', ' + info.get('country', 'error')


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

    print(f"IP: {ip}, Location: {location}, City: {city}, Region: {region}, Country: {country}")


if __name__ == '__main__':
    print(get_city())
