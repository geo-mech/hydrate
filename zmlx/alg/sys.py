# -*- coding: utf-8 -*-


def get_latest_version():
    """
    返回程序的最新的版本
    """
    try:
        try:
            from zml import data
            if data.has_tag_today('latest_version_checked'):
                txt = data.getenv('latest_version')
                if txt is not None:
                    if len(txt) == 6:
                        return int(txt)
        except:
            pass
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
            data.setenv('latest_version', version)
            data.add_tag_today('latest_version_checked')
            return int(version)
    except Exception as err:
        print(f'meet exception: {err}')
        return


if __name__ == '__main__':
    version = get_latest_version()
    print(type(version))
    print(f'version={version}')
