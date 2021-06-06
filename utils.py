import vtk
import os
import numpy as np
from numpy.linalg import inv


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
    points = np.array(np.meshgrid(bounds[:2], bounds[2:4], bounds[-2:], indexing="ij")).T.reshape(-1, 3)
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

