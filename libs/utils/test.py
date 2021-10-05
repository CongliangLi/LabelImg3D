from libs.utils.utils import *
import pandas as pd
import numpy as np
from cv2 import *

if __name__ == '__main__':
    txt_path = "G:/LINEMOD/ape/labels/000000.txt"
    img_path = "G:/LINEMOD/ape/JPEGImages/000000.jpg"
    txt = pd.read_table(txt_path, sep=' ', header=None)

    xs = list()
    ys = list()
    img = imread(img_path)
    h, w = img.shape[:2]
    for i in range(9):
        xs.append(int(txt[2 * i + 1][0] * w))
        ys.append(int(txt[2 * i + 2][0] * h))

    for i in range(9):
        cv2.circle(img, (xs[i], ys[i]), 2, (255, 0, 0), -1)
    imshow("img", img)
    waitKey(0)

    pass
