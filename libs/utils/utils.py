import vtk
import os
import numpy as np
from numpy.linalg import inv
import cv2
from math import atan, radians, degrees, cos, sin
import yaml
from plyfile import PlyData


def getTransform(matrix):
    transform = vtk.vtkTransform()
    transform.SetMatrix(matrix)
    return transform


def deepCopyTransform(transform):
    new_transform = vtk.vtkTransform()
    new_transform.DeepCopy(transform)
    return new_transform


def deepCopyMatrix(matrix):
    new_matrix = vtk.vtkMatrix4x4()
    new_matrix.DeepCopy(matrix)
    return new_matrix


def getInvert(matrix):
    invert_matrix = vtk.vtkMatrix4x4()
    matrix.Invert()
    invert_matrix.DeepCopy(matrix)
    matrix.Invert()
    return invert_matrix


def matrixMultiple(matrix_a, matrix_b):
    matrix = vtk.vtkMatrix4x4()
    vtk.vtkMatrix4x4.Multiply4x4(matrix_a, matrix_b, matrix)
    return matrix


def matrix2List(matrix, pre=4):
    return [round(matrix.GetElement(i, j), pre) for i in range(4) for j in range(4)]


def matrix2Numpy2D(matrix):
    return np.array([[matrix.GetElement(i, j) for i in range(4)] for j in range(4)])


def list2Matrix(data):
    matrix = vtk.vtkMatrix4x4()
    matrix.DeepCopy(data)
    return matrix


def getFiles(folder, filter):
    return [os.path.relpath(os.path.join(maindir, filename), folder) \
            for maindir, _, file_name_list in os.walk(folder, followlinks=True) \
            for filename in file_name_list if os.path.splitext(filename)[-1] in filter]


def worldToView(renderer, points):
    ret = []
    for p in points:
        q = [p[i] for i in range(3)] + [1]
        renderer.SetWorldPoint(q)
        renderer.WorldToView()
        ret.append(renderer.GetViewPoint())
    return ret


def getMatrixW2I(renderer, w, h):
    if renderer is None:
        return
    camera = renderer.GetActiveCamera()
    if camera is None:
        return

    # near, far = camera.GetClippingRange()
    # P_w2v = matrix2Numpy2D(
    #         camera.GetCompositeProjectionTransformMatrix(
    #             renderer.GetTiledAspectRatio(),
    #             -1, 1
    #         )
    #     )
    r = w / h
    # caculate the image region in the view
    i_w = np.array([[-0.5, 0.5 / r, 0], [0.5, -0.5 / r, 0]])
    # i_v = np.dot(P_w2v, cart2hom(i_w).T).T
    # i_v = (i_v / i_v[:, -1:])[:, :-1]
    i_v = np.array(worldToView(renderer, cart2hom(i_w)))
    w_i, h_i = abs(i_v[1, :2] - i_v[0, :2])
    # w_r, h_r = renderer.GetSize()
    # P_v2r = np.array([
    #     [w_r/2,     0,      w_r/2],
    #     [0,         -h_r/2, h_r/2],
    #     [0,         0,      1],
    # ])
    # i_r = np.dot(P_v2r, cart2hom(i_v[:, :2]).T).T
    # i_v = i_v / i_v[:, -2:-1]
    # l, t = i_r[0, :2]
    # r, b = i_r[1, :2]
    # w_i, h_i = r - l, b - t
    # get the view to image matrix
    # P_w2v = np.array([
    #         [2/w_i,     0,      0],
    #         [0,         2/h_i,  0],
    #         [0,         0,      1]
    # ])
    P_v2i = np.array([
        [w / w_i, 0, w / 2],
        [0, -h / h_i, h / 2],
        [0, 0, 1]
    ])
    # P_r2i = np.array([
    #         [w/(r-l),       0,          -w*l/(r-l)],
    #         [0,             h/(b-t),    -h*t/(b-t)],
    #         [0,             0,          1]
    # ])

    # P_w2i = np.dot(P_v2i, P_w2v[:3, :])
    # test_points = np.array([
    #     [0.5, 0, 0], [0, 0.5 / r, 0],
    #     [-0.5, 0, 0], [0, -0.5 / r, 0],
    #     [0.5/2, 0, 0], [0, 0.5 / r / 2, 0],
    #     [-0.5/2, 0, 0], [0, -0.5 / r / 2, 0],
    # ])
    # test_points = np.dot(P_w2i, cart2hom(test_points).T).T
    # print(test_points)
    return P_v2i


def getMatrixO2W(prop3D):
    """Get the tranform matrix from the object to the world

    Args:
        prop3D ([vtkActor]): Object Coordinates

    Returns:
        [numpy.array 4x4]: [The 4x4 matrix which can transform from the object coordinate to the world coordinate]
    """
    return matrix2Numpy2D(prop3D.GetMatrix()).T


def object2World(prop3D, points):
    mat = getMatrixO2W(prop3D)
    points = cart2hom(points)
    return hom2cart(np.matmul(mat, points.T).T)


def setActorMatrix(prop3D, matrix):
    """Set the vtk actor matrix

    Args:
        prop3D ([vtkActor]): The actor to be set
        matrix ([vtkMatrix4x4]): The matrix
    """
    transform = getTransform(matrix)
    prop3D.SetOrientation(transform.GetOrientation())
    prop3D.SetPosition(transform.GetPosition())
    prop3D.SetScale(transform.GetScale())
    prop3D.Modified()


def getActorLocalBounds(prop3D):
    mat = vtk.vtkMatrix4x4()
    mat.DeepCopy(prop3D.GetMatrix())
    setActorMatrix(prop3D, vtk.vtkMatrix4x4())
    bounds = prop3D.GetBounds()
    setActorMatrix(prop3D, mat)
    return bounds


def getActorRotatedBounds(prop3D):
    """Get the rotated bounds of an actor descriped by 8 points

    Args:
        prop3D (vtkActor): the target actor

    Returns:
        [np.array 8x3]: actor rotated bounds
    """
    bounds = getActorLocalBounds(prop3D)
    points = np.array(np.meshgrid(bounds[:2], bounds[2:4], bounds[-2:])).T.reshape(-1, 3)
    return object2World(prop3D, points)
    # return np.ones((8, 3))


def getActorXYZRange(prop3D):
    bounds = getActorLocalBounds(prop3D)
    return (bounds[2 * i + 1] - bounds[2 * i] for i in range(3))


def getActorXYZAxis(prop3D):
    points = np.vstack((np.identity(3), [0, 0, 0]))
    points = object2World(prop3D, points)
    return points[:3, :] - points[-1, :]


def worldToViewBBox(renderer, points):
    display_points = worldToView(renderer, points)
    display_points = np.array(display_points)
    min_x, min_y, _ = tuple(display_points.min(axis=0))
    max_x, max_y, _ = tuple(display_points.max(axis=0))
    return min_x, min_y, max_x, max_y


def listRound(arr, pre=4):
    return [round(d, pre) for d in arr]


def cart2hom(pts_3d):
    """ Input: nx3 points in Cartesian
        Oupput: nx4 points in Homogeneous by pending 1
    """
    assert len(pts_3d.shape) == 2
    n = pts_3d.shape[0]
    pts_3d_hom = np.hstack((pts_3d, np.ones((n, 1))))
    return pts_3d_hom


def hom2cart(pts_3d):
    assert len(pts_3d.shape) == 2
    return pts_3d[:, :-1]


def getAngle(x, y):
    return np.arctan2(
        (np.cross(x, y) / (np.linalg.norm(x) * np.linalg.norm(y))).sum(),
        (np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y))).sum()
    )


def draw_projected_box3d(image, qs, color=[(255, 0, 0), (0, 0, 255), (0, 255, 0)],
                         thickness=2):
    """ Draw 3d bounding box in image
        qs: (8,3) array of vertices for the 3d box in following order:
            1 -------- 0
           /|         /|
          2 -------- 3 .
          | |        | |
          . 5 -------- 4
          |/         |/
          6 -------- 7
    """
    if qs is None:
        return image
    qs = qs[[7, 5, 4, 6, 3, 1, 0, 2], :].astype(np.int32)
    for k in range(0, 4):
        # Ref: http://docs.enthought.com/mayavi/mayavi/auto/mlab_helper_functions.html
        i, j = k, (k + 1) % 4
        # use LINE_AA for opencv3
        # cv2.line(image, (qs[i,0],qs[i,1]), (qs[j,0],qs[j,1]), color, thickness, cv2.CV_AA)
        cv2.line(image, (qs[i, 0], qs[i, 1]), (qs[j, 0], qs[j, 1]), color[0], thickness)
        i, j = k + 4, (k + 1) % 4 + 4
        cv2.line(image, (qs[i, 0], qs[i, 1]), (qs[j, 0], qs[j, 1]), color[1], thickness)

        i, j = k, k + 4
        cv2.line(image, (qs[i, 0], qs[i, 1]), (qs[j, 0], qs[j, 1]), color[2], max(1, thickness // 2))
    return image


def drawProjected3DBox(renderer, prop3D, img, with_clip=False):
    h, w, _ = img.shape
    P_v2i = getMatrixW2I(renderer, w, h)
    pts_3d = getActorRotatedBounds(prop3D)
    # pts_3d = np.array([
    #     [0.5, 0, 0], [0, 0.5 / r, 0],
    #     [-0.5, 0, 0], [0, -0.5 / r, 0],
    #     [0.5/2, 0, 0], [0, 0.5 / r / 2, 0],
    #     [-0.5/2, 0, 0], [0, -0.5 / r / 2, 0],
    # ])
    p_v = np.array(worldToView(renderer, pts_3d))
    # p_v = (p_v / p_v[:, -1:])[:, :3]
    # p_v = p_v * 1 / P_w2v[-1, -1] / p_v[:, -1:]
    # p_r = np.dot(P_v2r, cart2hom(p_v[:, :2]).T).T
    p_i = np.dot(P_v2i, cart2hom(p_v[:, :2]).T).T[:, :2]
    # p_i = (p_i / p_i[:, -1:])[:, :2]
    # p_v = np.dot(P_w2v, cart2hom(pts_3d).T).T
    # p_i = np.dot(P_v2i, cart2hom(p_v[:, :-2]).T).T
    # pts_2d = (pts_2d / pts_2d[:, -1:])[:, :3]
    # pts_2d = (np.dot(P_v2i, pts_2d.T).T)
    # pts_2d = (pts_2d / pts_2d[:, -1:])[:, :2]
    # pts_2d = (pts_2d / pts_2d[:, -1:])[:, :3]
    # pts_2d = np.dot(P_v2i, pts_2d.T).T
    # pts_2d = (pts_2d / pts_2d[:, -1:])[:, :2]
    # P_w2i = np.dot(P_v2i, P_w2v[:-1, :])
    # pts_3d = getActorRotatedBounds(prop3D)
    # pts_2d = np.dot(P_w2i, cart2hom(pts_3d).T).T
    # pts_2d = (pts_2d / pts_2d[:, -1:])[:, :2]
    image = draw_projected_box3d(img.copy(), p_i[:, :2])
    if with_clip:
        l, t = (p_i.min(axis=0).astype(int) - 5).clip(0)
        r, b = (p_i.max(axis=0).astype(int) + 5).clip(0)
        return image[t:b, l:r, :]
    return image


def reconnect(signal, newhandler=None, oldhandler=None):
    try:
        if oldhandler is not None:
            while True:
                signal.disconnect(oldhandler)
        else:
            signal.disconnect()
    except TypeError:
        pass
    if newhandler is not None:
        signal.connect(newhandler)


def get_all_path(open_file_path):
    rootdir = open_file_path
    path_list = []
    list = os.listdir(rootdir)
    for i in range(0, len(list)):
        com_path = os.path.join(rootdir, list[i])
        if os.path.isfile(com_path):
            path_list.append(com_path)
        if os.path.isdir(com_path):
            path_list.extend(get_all_path(com_path))
    return path_list


def get_dirname(path):
    """

    Args:
        path: dir path

    Returns:
        dir_name: all dir names in the file path

    """
    dir_path = []
    for lists in os.listdir(path):
        sub_path = os.path.join(path, lists)
        if os.path.isdir(sub_path):
            dir_path.append(sub_path)

    return dir_path


# Solve the problem that opencv can't read Chinese path
def cv_imread(filepath):
    img = cv2.imdecode(np.fromfile(filepath, dtype=np.uint8), -1)
    return img


# get cot of angle system
def cot(angle):
    angle = radians(angle)
    return cos(angle) / sin(angle)


# Calculating distance from fov(angle value)
def get_distance(fov):
    return round(1 / 2 * cot(fov / 2), 2)


# Calculating fov(angle value) from distance
def get_fov(distance):
    return round(2 * atan(1 / (2 * distance)), 2)


# parse yaml to dict
def parse_yaml(yaml_path):
    """
   Reads a yaml file
    Args:
        yaml_path: Path to the yaml file
    Returns:
        yaml_dic: Dictionary containing the yaml file content

    """

    if not os.path.isfile(yaml_path):
        print("Error: file {} does not exist!".format(yaml_path))
        return None

    with open(yaml_path) as fid:
        yaml_dic = yaml.safe_load(fid)

    return yaml_dic


# Calculating camera intrinsics from fov and image size
def get_camera_intrinsics(fov_h, img_size):
    """

    Args:
        fov_h: horizontal fov of camera
        img_size: image_size [w,h]

    Returns:
        camera intrinsics matrix（3*3）

    """
    w, h = img_size
    f = round(w / 2 * cot(fov_h / 2), 2)
    fov_v = 2 * atan(h / (2 * f))

    cx = w / 2
    cy = h / 2

    camera_intrinsics = [f, 0, cx,
                         0, f, cy,
                         0, 0, 1]

    return camera_intrinsics


def get_R_obj2w(model_matrix):
    """

    Args:
        model_matrix: model matrix of annotations  shape:(16,) or (4,4)

    Returns: Rotation matrix for object to world  (3,3)

    """
    if model_matrix.shape == (16,):
        model_matrix = model_matrix.reshape(4, 4)

    return model_matrix[:3, : 3]


def get_R_w2c():
    """

    Returns: Rotation matrix for world to camera (3,3)

    """
    return np.dot(np.dot(Rotate_y_axis(180), Rotate_z_axis(-90)), np.array([[0., 1., 0.], [-1., 0., 0.], [0., 0., 1.]]))


def get_R_obj2c(model_matrix):
    """

    Args:
        model_matrix: model matrix of annotations  shape:(16,) or (4,4)

    Returns: Rotation matrix for object to camera  (3,3)

    """
    # return np.dot(get_R_obj2w(model_matrix), get_R_w2c())
    return np.dot(get_R_w2c(), get_R_obj2w(model_matrix))


def get_T_obj2w(model_matrix):
    """

    Args:
        model_matrix: model matrix of annotations  shape:(16,) or (4,4)

    Returns: Rotation matrix for object to world  (shape:(1,3) unit:meter)

    """
    if model_matrix.shape == (16,):
        model_matrix = model_matrix.reshape(4, 4)

    return np.concatenate((-model_matrix[:2, -1], [model_matrix[2, -1]]))


def get_T_w2c(fov):
    """

    Args:
        fov: camera fov (angle value)

    Returns: Translocation matrix of world to camera   (shape:(1,3) unit:meter)

    """
    return np.array([0, 0, -get_distance(fov)])


def get_T_obj2c(model_matrix, fov):
    """

    Args:
        model_matrix: model matrix of annotations  shape:(16,) or (4,4)
        fov: camera fov (angle value)

    Returns: Translocation matrix of world to camera (shape:(1,3) unit:meter)

    """
    return get_T_obj2w(model_matrix) + get_T_w2c(fov)


def get_T_obj_bottom2center(obj_size):
    """

    Args:
        obj_size: obj size (x,y,z) unit:meter

    Returns: Translocation matrix from bottom to center (shape:(1,3) unit:meter)

    """
    return np.array([0, 0, obj_size[2] / 2])


def load_model_ply(path_to_ply_file):
    """
   Loads a 3D model from a plyfile
    Args:
        path_to_ply_file: Path to the ply file containing the object's 3D model
    Returns:
        points_3d: numpy array with shape (num_3D_points, 3) containing the x-, y- and z-coordinates of all 3D model points

    """
    model_data = PlyData.read(path_to_ply_file)
    vertex = model_data['vertex']
    points_3d = np.stack([vertex[:]['x'], vertex[:]['y'], vertex[:]['z']], axis=-1)
    return points_3d


def load_model_ply(path_to_ply_file):
    """
   Loads a 3D model from a plyfile
    Args:
        path_to_ply_file: Path to the ply file containing the object's 3D model
    Returns:
        points_3d: numpy array with shape (num_3D_points, 3) containing the x-, y- and z-coordinates of all 3D model points

    """
    model_data = PlyData.read(path_to_ply_file)
    vertex = model_data['vertex']
    points_3d = np.stack([vertex[:]['x'], vertex[:]['y'], vertex[:]['z']], axis=-1)
    return points_3d


def Rotate_x_axis(theta):
    """

    Args:
        theta: angle value

    Returns: the matrix (3,3)

    """
    theta = radians(theta)
    return np.array([[1., 0., 0.], [0., cos(theta), -sin(theta)], [0., sin(theta), cos(theta)]])


def Rotate_y_axis(theta):
    """

    Args:
        theta: angle value

    Returns: the matrix (3,3)

    """
    theta = radians(theta)
    return np.array([[cos(theta), 0., sin(theta)], [0., 1., 0.], [-sin(theta), 0., cos(theta)]])


def Rotate_z_axis(theta):
    """

    Args:
        theta: angle value

    Returns: the matrix (3,3)

    """
    theta = radians(theta)
    return np.array([[cos(theta), -sin(theta), 0.], [sin(theta), cos(theta), 0.], [0., 0., 1.]])


def rotation_mat_to_axis_angle(rotation_matrix):
    """
    Computes an axis angle rotation vector from a rotation matrix
    Arguments:
        rotation_matrix: numpy array with shape (3, 3) containing the rotation
    Returns:
        axis_angle: numpy array with shape (3,) containing the rotation
    """
    axis_angle, jacobian = cv2.Rodrigues(rotation_matrix)

    return np.squeeze(axis_angle)


def axis_angle_to_rotation_mat(rotation_vector):
    """
    Computes a rotation matrix from an axis angle rotation vector
    Arguments:
        rotation_vector: numpy array with shape (3,) containing the rotation
    Returns:
        rotation_mat: numpy array with shape (3, 3) containing the rotation
    """
    rotation_mat, jacobian = cv2.Rodrigues(np.expand_dims(rotation_vector, axis=-1))

    return rotation_mat


def draw_box(image, box, color=(255, 255, 0), thickness=1):
    """ Draws a box on an image with a given color.

    # Arguments
        image     : The image to draw on.
        box       : A list of 4 elements (x1, y1, x2, y2).
        color     : The color of the box.
        thickness : The thickness of the lines to draw a box with.
    """
    b = np.array(box).astype(int)
    cv2.rectangle(image, (b[0], b[1]), (b[2], b[3]), color, thickness, cv2.LINE_AA)
    return image
