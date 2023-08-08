from zmlx.filesys.path import join as join_paths

if __name__ == '__main__':
    print(join_paths('x', 'y'))
    print(join_paths('x', 'y', None))
