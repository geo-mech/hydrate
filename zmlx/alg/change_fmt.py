from zmlx.filesys.change_fmt import *

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        key = sys.argv[1]
        path = None
        if len(sys.argv) >= 3:
            path = sys.argv[2]
        if key == 'seepage2txt':
            seepage2txt(path)

        if key == 'txt2seepage':
            txt2seepage(path)
