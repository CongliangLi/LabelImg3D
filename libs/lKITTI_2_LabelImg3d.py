import os
from libs.utils import roty
import numpy as np
import pandas as pd


def KITTI_2_LabelImg3D(label_path, c_distance):
    a = pd.read_table(label_path, sep=' ', header=None)
    model_data = {}
    data = {}
    for i in range(0, len(a)):
        obj_class = a[0][i]
        obj_position_c = [a[i][i] for i in range(11, 14)]
        obj_position_w = [obj_position_c[0], -obj_position_c[1], -(obj_position_c[2] - c_distance)]
        obj_alpha = a[3][i]
        R_oL2oK = [[0, -1, 0],  # Rotate 90 degrees clockwise around the X axis
                   [1, 0, 0],
                   [0, 0, 1]]

        obj_r_y = a[14][i]
        R_oK2c = roty(obj_r_y)
        R_c2w_1 = [[0, -1, 0],
                   [1, 0, 0],
                   [0, 0, 1]]
        R_c2w_2 = [[1, 0, 0],
                   [0, -1, 0],
                   [0, 0, -1]]
        R_c2w = np.dot(R_c2w_1, R_c2w_2)
        R_oL2w = np.dot(np.dot(R_oL2oK, R_oK2c), R_c2w)


    pass


if __name__ == '__main__':
    label_path = 'F:/my_desktop/PycharmFiles/3D_detection/labelimg3d/scenes/000025.txt'
    distance = 0.52
    KITTI_2_LabelImg3D(label_path, distance)
