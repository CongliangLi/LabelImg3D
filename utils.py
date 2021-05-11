import vtk
import os
importn numpy as np

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

def matrix2List(matrix):
    return [matrix.GetElement(i, j) for i in range(4) for j in range(4)]

def list2Matrix(data):
    matrix = vtk.vtkMatrix4x4()
    matrix.DeepCopy(data)
    return matrix


def getFiles(folder, filter):
    return [os.path.relpath(os.path.join(maindir, filename), folder) \
            for maindir, _, file_name_list in os.walk(folder, followlinks=True) \
            for filename in file_name_list if os.path.splitext(filename)[-1] in filter]
