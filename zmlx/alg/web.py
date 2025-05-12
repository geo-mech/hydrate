"""
网页相关的操作。直接从webbrowser导入即可
"""
from webbrowser import open_new_tab, open, open_new

__all__ = ['open_new_tab', 'open', 'open_new']

if __name__ == '__main__':
    open_new_tab('https://gitee.com/geomech/hydrate')
