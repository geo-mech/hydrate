from zmlx import *


def main():
    mesh = Mesh3('mesh.xml')
    print(mesh)
    print(mesh.get_link(0).length)
    print(mesh.get_face(0).area)
    print(mesh.get_body(0).volume)


if __name__ == '__main__':
    main()
