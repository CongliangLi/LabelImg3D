from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys, os
import numpy as np
import vtk, qimage2ndarray

class vtkLabel(QLabel):
    def __init__(self):
        super(vtkLabel, self).__init__()
        cone = vtk.vtkConeSource()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(cone.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        ren = vtk.vtkRenderer()
        ren.AddActor(actor)
        renWin = vtk.vtkRenderWindow()
        renWin.AddRenderer(ren)
        renWin.SetOffScreenRendering(1)
        imageFilter = vtk.vtkWindowToImageFilter()
        imageFilter.SetInput(renWin)

        self.ren = ren
        self.renWin = renWin
        self.imageFilter = imageFilter

    def mousePressEvent(self, QMouseEvent):
        super().mousePressEvent(QMouseEvent)
        pos = QMouseEvent.pos()
        x = pos.x()
        y = pos.y()
        self.lastPos = [x, y]


    def mouseReleaseEvent(self, QMouseEvent):
        super().mouseReleaseEvent(QMouseEvent)
        self.lastPos = None

    def mouseMoveEvent(self, QMouseEvent):
        super().mouseMoveEvent(QMouseEvent)
        pos = QMouseEvent.pos()
        x = pos.x()
        y = pos.y()
        if self.lastPos != None:
            if QMouseEvent.buttons() == Qt.RightButton:
                dy = self.lastPos[1] - y
                center = self.ren.GetCenter()
                dyf = dy/center[1]
                import math
                val = math.pow(1.1, dyf)
                self.ren.GetActiveCamera().Dolly(val)

            if QMouseEvent.buttons() == Qt.LeftButton:
                dx = x - self.lastPos[0]
                dy = self.lastPos[1] - y
                size = self.renWin.GetSize()

                delta_elevation = -20.0 / size[1]
                delta_azimuth = -20.0 / size[0]
                rxf = dx * delta_azimuth
                ryf = dy * delta_elevation

                camera = self.ren.GetActiveCamera()
                camera.Azimuth(rxf)
                camera.Elevation(ryf)
                camera.OrthogonalizeViewUp()

            self.ren.ResetCameraClippingRange()
            self.ren.UpdateLightsGeometryToFollowCamera()
            self.ren.Render()
            self.calculationForDisplay()

    def resizeEvent(self, QMouseEvent):
        super().resizeEvent(QMouseEvent)
        self.renWin.SetSize(self.width(), self.height())
        self.calculationForDisplay()
        picker = vtk.vtkPropPicker()
        picker.Pick(250, 250, 0, self.ren)
        if picker.GetActor():
            coordinate = vtk.vtkCoordinate()
            coordinate.SetCoordinateSystemToDisplay()
            coordinate.SetValue(250, 250, 0)
            position = coordinate.GetComputedWorldValue(self.ren)
            self.position = position
            print('the point is one of the cone point')
        else:
            raise RuntimeError('the point is not one of the cone point')

    def calculationForDisplay(self):
        self.renWin.Render()
        self.imageFilter.Modified()
        self.imageFilter.Update()
        displayImg = self.imageFilter.GetOutput()

        dims = displayImg.GetDimensions()
        from vtk.util.numpy_support import vtk_to_numpy
        numImg = vtk_to_numpy(displayImg.GetPointData().GetScalars())
        numImg = numImg.reshape(dims[1], dims[0], 3)
        numImg = numImg.transpose(0, 1, 2)
        numImg = np.flipud(numImg)

        displayQImg = qimage2ndarray.array2qimage(numImg)
        pixmap = QPixmap.fromImage(displayQImg)
        self.pixmap = pixmap
        self.update()

    def paintEvent(self, QPaintEvent):
        super(vtkLabel, self).paintEvent(QPaintEvent)
        painter = QPainter(self)
        width = self.width()
        height = self.height()
        painter.drawPixmap(QPoint(0, 0), self.pixmap, QRect(0, 0, width, height))

        coordinate = vtk.vtkCoordinate()
        coordinate.SetCoordinateSystemToWorld()
        point = self.position
        coordinate.SetValue(point[0], point[1], point[2])
        displayCoor = coordinate.GetComputedDisplayValue(self.ren)
        x = displayCoor[0]
        y = displayCoor[1]
        y = self.height() - y
        painter.setPen(QPen(QColor(255, 0, 0), 5))
        painter.drawPoint(x, y)

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.resize(500,500)
        self.imageLabel = vtkLabel()
        self.setCentralWidget(self.imageLabel)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()