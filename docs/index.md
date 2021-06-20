# Purpose

LabelImg3D is an annotation tools for labeling the 3D model in the image, in order to get the extrinsic parameter between the camera and the 3D model.

> add some gif to show how this works

# Introduction

The LabelImg3D is a first of its kind label tools for building the extrinsic parameter estimation dataset. You can easily use multiple 3D models (such as, vehicle, truck, bus, etc.) to label the 2D bounding boxes, 3D bounding boxes in both image space and 3D space, 3D model in one app.

So how to use the app, there are four steps:
1. collect your image dataset (i.e. UA-DETRAC, MOT)
2. collect your 3D model dataset
3. organize these dataset as the following file tree:

```
|---Scene
    |---annotations           ---> this tools will generate
        |---<image_name>1.json
        |---<image_name>2.json
        |---...
    |---images                ---> your collected image dataset
        |---<image_name>1.jpg
        |---<image_name>2.jpg
        |---...
    |---models                ---> your collected model dataset
        |---<model_name>1.obj
        |---<model_name>2.obj
        |---...
```
4. open the app, click the menue File-->Open
5. label each image, the annotation file will automatically generated when you move to the other images

# Installation
## Install from pip

> try to support the installation from the pip


## Install by the installer
Only for windows user.

You can download the installer from `todo`

