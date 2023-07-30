def point_distance(p1, p2):
    """
    Returns the distance between two points
    """
    dist = 0.0
    for i in range(min(len(p1), len(p2))):
        dist += (p1[i] - p2[i]) ** 2
    return dist ** 0.5


if __name__ == '__main__':
    print(point_distance(p1=(0, 0, 0), p2=(1, 0, 0)))
