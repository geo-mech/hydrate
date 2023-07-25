import warnings

try:
    from zml import app_data
except:
    app_data = None
    warnings.warn('can not get app_data from zml')


def get_latest_version():
    """
    返回程序的最新的版本
    """
    try:
        if app_data is not None:
            if app_data.has_tag_today('latest_version_checked'):
                txt = app_data.getenv('latest_version')
                if txt is not None:
                    if len(txt) == 6:
                        return int(txt)
        url = 'https://gitee.com/geomech/hydrate'
        from urllib.request import urlopen
        import ssl  # using context
        # text = '搜索如下关键词： ZmlVersion=221019 '
        text = urlopen(url, context=ssl._create_unverified_context()
                       ).read().decode("utf-8")
        import re
        result = re.findall(r'(\w+)=(\d+)', text)
        version = dict(result).get('ZmlVersion')
        if version is not None:
            if app_data is not None:
                app_data.setenv('latest_version', version)
                app_data.add_tag_today('latest_version_checked')
            return int(version)
    except Exception as err:
        warnings.warn(f'meet exception <{err}> when run <{get_latest_version}>')
        return


if __name__ == '__main__':
    version = get_latest_version()
    print(type(version))
    print(f'version={version}')
