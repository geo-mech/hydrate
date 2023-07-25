from zml import is_array


def make_index(index):
    if is_array(index):
        return index
    else:
        return index,


if __name__ == '__main__':
    print(make_index(1))
    print(make_index((1, 2)))
