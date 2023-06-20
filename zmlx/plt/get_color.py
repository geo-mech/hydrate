def get_color(cmap, lr, rr, val):
    """
    对于给定的colormap，数值的范围和给定的数值，返回给定的数值所对应的颜色
    """
    assert cmap.N >= 2
    if lr >= rr:
        return cmap(int(cmap.N / 2))
    assert lr < rr
    if val <= lr:
        return cmap(0)
    if val >= rr:
        return cmap(cmap.N - 1)
    i = max(0, min(cmap.N - 1, int((val - lr) * cmap.N / max(rr - lr, 1.0e-100))))
    return cmap(i)
