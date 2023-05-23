def reset_injectors(seepage):
    """
    重置一下injector，使得在下一次迭代的时候，可以重新去确定injector需要连接的Cell的ID
    """
    for inj in seepage.injectors:
        inj.cell_id = seepage.cell_number
