"""数据资源目录。

Modified by Claude, 2026-08-12
"""
import sys

from zmlx.data.igg import load_igg  # 加载igg.png
from zmlx.data.mesh_c10000 import get_face_centered_seepage_mesh as create_c10000
from zmlx.exts import SelfPath

get_path = SelfPath(__file__)


def read_doc(name):
    """读取随包发布的文档（``README.md`` / ``CHANGELOG.md`` / ``ROADMAP.md``）的文本。

    ⚠️ 这些文件**只存在于本目录**：仓库根目录下的同名文件已删除，因此不再需要任何
    「同步」步骤 —— 开发环境与 pip 安装环境读到的是同一份（``package-data`` 里
    ``"zmlx" = ["**/*"]`` 会把它们打进 wheel）。

    ⚠️ 相应地，改动仓库根目录的 ``README.md`` 之后，**必须手动把
    ``zmlx/data/README.md`` 刷新一份** —— 以前由 ``zmlx/ui/data/md_sync.py`` 自动
    复制，那个模块已删除（它服务的三份文档里只剩 README 需要同步，且 README 极少改，
    交给 agent 复制即可）。

    Args:
        name: 文件名，例如 ``'CHANGELOG.md'``。

    Returns:
        str: 文件文本；文件不存在或读不出来时返回 ``None``。
    """
    import os

    from zmlx.system import read_text

    path = get_path(name)
    if not os.path.isfile(path):
        return None
    try:
        text = read_text(path=path, encoding='utf-8')
        if text is None:
            # 编码兜底: 用系统默认编码再试一次
            text = read_text(path=path)
        return text
    except Exception as err:
        print(f'Error: {err}', file=sys.stderr)
        return None


if __name__ == "__main__":
    print(get_path())
