import os
import utils
import json
import math
import numpy as np
import cv2 as cv

def get_image_name_list(path):
    name_list = []
    for file in os.listdir(path):
        name_list.append(os.path.splitext(file)[0])
    return name_list


if __name__ == '__main__':
    xml_path = "D:/TemporaryDocument/UA-DETRAC/DETRAC-Train-Annotations-XML/"
    image_path = "D:/TemporaryDocument/UA-DETRAC/Insight-MVT_Annotation_Train/"
    image_save_root_path = "D:/TemporaryDocument/UA-DETRAC/new_image"

    for xml in os.listdir(xml_path):
        name = os.path.splitext(xml)[0]

        all_frames = utils.read_mot_file(os.path.join(xml_path, xml))
        image_name_list = get_image_name_list(os.path.join(image_path, name))

        for i, frame in enumerate(all_frames):
            image_name = image_name_list[i] + ".jpg"
            image_save_path = os.path.join(image_save_root_path, name)
            if not os.path.exists(image_save_path):
                os.makedirs(image_save_path)
            image = cv.imread(os.path.join(image_path, name, image_name))

            for j, target in enumerate(frame):
                image_points = target["bbox_2d"]
                img = utils.draw_box(image, image_points, (0, 0, 255))
                cv.imwrite(os.path.join(image_save_path, image_name), img)
