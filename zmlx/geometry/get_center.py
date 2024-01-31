def get_center(p1, p2):
    return [(p1[i] + p2[i]) * 0.5 for i in range(min(len(p1), len(p2)))]


if __name__ == '__main__':
    print(get_center(p1=(0, 0, 0), p2=(1, 0, 0)))
