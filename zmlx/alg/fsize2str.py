def fsize2str(size):
    size /= 1024
    if size < 2000:
        return '%0.2f kb' % size

    size /= 1024
    if size < 2000:
        return '%0.2f Mb' % size

    size /= 1024
    if size < 2000:
        return '%0.2f Gb' % size
    else:
        size /= 1024
        return '%0.2f Tb' % size
