# Introduction

LabelImg3D is the first-of-its-kind tool to annotate images with 3D models, which allows you to reconstruct 3D scenes from images. It provides visual annotation operations. You can easily build a 3D dataset from 2D one like MOT15-20, UA-detrac, etc. just to find some corresponding 3D models (like pedestrians, vehicles, trucks, etc.) to perform 3D object detection, 3D object tracking and 3D object reconstruction.

![](../imgs/demo.gif)

How to use the app, there are four steps:

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