from zml import *

core.use(None, 'img2trimesh', c_char_p, c_char_p, c_char_p,
         c_char_p, c_char_p, c_size_t)


def img2trimesh(verfile, linkfile, trifile, imgpath, summary_path, trin):
    """
    Convert a matrix information into a triangular mesh
    """
    core.img2trimesh(make_c_char_p(verfile), make_c_char_p(linkfile),
                     make_c_char_p(trifile), make_c_char_p(imgpath),
                     make_c_char_p(summary_path), trin)
