from zmlx.data.igg import load_igg  # 加载igg.png
from zmlx.data.mesh_c10000 import get_face_centered_seepage_mesh as create_c10000
from zmlx.exts import SelfPath

get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())
