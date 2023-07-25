def get_norm(p):
    """
    Returns the distance from the origin
    """
    assert len(p) > 0
    dist = p[0] ** 2
    for i in range(1, len(p)):
        dist += p[i] ** 2
    return dist ** 0.5
