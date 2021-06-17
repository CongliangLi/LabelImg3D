import vtk
import os
import numpy as np
from numpy.linalg import inv
import cv2


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
    P_w2v = matrix2Numpy2D(
            camera.GetCompositeProjectionTransformMatrix(
                renderer.GetTiledAspectRatio(),
                0, 1
            )
        )
    r = w / h
    # caculate the image region in the view
    i_w = np.array([[-0.5, 0.5 / r, 0], [0.5, -0.5 / r, 0]])
    i_v = np.dot(P_w2v, cart2hom(i_w).T).T
    i_v = i_v / i_v[:, -1:]
    # i_v = i_v / i_v[:, -2:-1]
    w_i, h_i, _, _ = abs(i_v[0, :] - i_v[1, :])
    # get the view to image matrix
    # P_w2v = np.array([
    #         [2/w_i,     0,      0],
    #         [0,         2/h_i,  0],
    #         [0,         0,      1]
    # ])
    P_v2i = np.array([
            [w/w_i*0.85,         0,          w/2],
            [0,             -h/h_i*0.85,     h/2],
            [0,             0,          1]
    ])

    # P_w2i = np.dot(P_v2i, P_w2v[:3, :])
    # test_points = np.array([
    #     [0.5, 0, 0], [0, 0.5 / r, 0],
    #     [-0.5, 0, 0], [0, -0.5 / r, 0],
    #     [0.5/2, 0, 0], [0, 0.5 / r / 2, 0],
    #     [-0.5/2, 0, 0], [0, -0.5 / r / 2, 0],
    # ])
    # test_points = np.dot(P_w2i, cart2hom(test_points).T).T
    # print(test_points)
    return P_w2v, P_v2i


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
    return (bounds[2*i+1] - bounds[2*i] for i in range(3))

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
        (np.cross(x, y) / (np.linalg.norm(x)*np.linalg.norm(y))).sum(),
        (np.dot(x, y) / (np.linalg.norm(x)*np.linalg.norm(y))).sum()
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
        cv2.line(image, (qs[i, 0], qs[i, 1]), (qs[j, 0], qs[j, 1]), color[2], max(1, thickness//2))
    return image

def drawProjected3DBox(renderer, prop3D, img, with_clip=False):
    h, w, _ = img.shape
    P_w2v, P_v2i = getMatrixW2I(renderer, w, h)
    pts_3d = getActorRotatedBounds(prop3D)
    # pts_3d = np.array([
    #     [0.5, 0, 0], [0, 0.5 / r, 0],
    #     [-0.5, 0, 0], [0, -0.5 / r, 0],
    #     [0.5/2, 0, 0], [0, 0.5 / r / 2, 0],
    #     [-0.5/2, 0, 0], [0, -0.5 / r / 2, 0],
    # ])
    p_v = np.dot(P_w2v, cart2hom(pts_3d).T).T
    p_v = (p_v / p_v[:, -1:])[:, :3]
    # p_v = p_v * 1 / P_w2v[-1, -1] / p_v[:, -1:]
    p_i = np.dot(P_v2i, p_v.T).T
    p_i = (p_i / p_i[:, -1:])[:, :2]
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
        l, t = p_i.min(axis=0).astype(int).clip(0)
        r, b = p_i.max(axis=0).astype(int).clip(0)
        return image[t:b, l:r, :]
    return image