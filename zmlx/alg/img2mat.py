def img2mat(fmat, fsummary, fimg):
    """
    Convert the image to a matrix. Where fimg is the storage path of the image,
    fmat is the file path where the matrix data is stored, and fsummary stores the index of all colors in the image
    """
    from PIL import Image
    import numpy as np
    img = np.array(Image.open(fimg))
    print(f'Succeed open image {fimg}, shape is {img.shape}')
    rows, cols, dims = img.shape
    assert 1 <= dims <= 4

    indexes = np.zeros(shape=(rows, cols), dtype=np.int32)
    color_dict = {}
    for ir in range(rows):
        for ic in range(cols):
            c = f'{img[ir, ic, :]}'
            if c in color_dict.keys():
                indexes[ir, ic] = color_dict[c]
            else:
                ind = len(color_dict)
                color_dict[c] = ind
                indexes[ir, ic] = ind
    print('Succeed parsed pixels')
    np.savetxt(fmat, indexes, fmt='%d')
    with open(fsummary, 'w') as file:
        for (key, value) in color_dict.items():
            file.write(f'{value} {key}\n')
            print(f'   Ind = {value}, Color = {key}')
    print(f'Succeed output to {fmat} and {fsummary}')
