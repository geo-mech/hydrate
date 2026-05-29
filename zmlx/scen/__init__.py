"""
定义具体的应用场景（scenario）：具体需要解决的问题。基于zmlx中的其它模块，实现最接近应用的功能配置。
这里的每一个子模块，都是针对具体应用场景的、可能有用的代码的集合。

除了hydrate和icp这两个之前已经导入到zmlx顶层的包之外，后续其他的包，都采用松散的组织方式，不再导入到
zmlx和zmlx.scen中。因此，scen中的子包，可以存放其他不成熟以及测试中的代码。

为了避免可能的代码污染，在这里，不再导入scen中的子包中的任何代码。
"""

from zmlx.exts import SelfPath

get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())
