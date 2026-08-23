"""化学反应模块（水合物、相变、燃烧、溶解等反应定义）.

Modified by Claude, 2026-08-12
"""
from zmlx.exts import SelfPath
from zmlx.react.alg import load_reactions, add_reaction, create_reaction
from zmlx.react.inh import create_inh, add_inh

get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())
