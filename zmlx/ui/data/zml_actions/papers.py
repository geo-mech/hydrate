menu = '帮助'
text = '已发表文章'
icon = 'pdf'


def slot():
    from zmlx.ui.alg import open_url
    open_url(url="https://pan.cstcloud.cn/s/5cKaQrdFSHM",
             use_web_engine=False)
