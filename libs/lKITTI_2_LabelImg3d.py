import os
from libs.utils import roty
import numpy as np
import pandas as pd


def KITTI_2_LabelImg3D(label_path):
    a = pd.read_table(label_path, sep=' ', header=None)
    obj_class = a[0][0]
    obj_position_c = [a[i][0] for i in range(10, 13)]
    obj_alpha = a[3][0]
    obj_r_y = a[14][0]
    R_o2c = roty(obj_r_y)
    R_c2_w = [[1, 0, 0],
              [0, 1, 0],
              [0, 0, 1]]

    pass


if __name__ == '__main__':
    label_path = 'F:/my_desktop/PycharmFiles/3D_detection/labelimg3d/KITTI/label_2/000000.txt'
    KITTI_2_LabelImg3D(label_path)
