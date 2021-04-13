import os

class V3PDataset:
    def __init__(self, scene_folder):
        self.scene_folder = scene_folder
        self.scene_folder = ''
        # self.images_folder = ''
        self.models_folder = ''

        self.image_name_list = []
        self.model_name_list = []

        self.open()


    def open(self):
        # 1. get all the images
        self.images_folder = os.path.join(self.scene_folder, 'images')
        self.image_name_list = getFiles(self.images_folder, ['.jpg'])
        
        # 2. get all the annotations
        self.annotations_folder = os.path.join(self.scene_folder, 'annotations')
        self.annotation_name_list = getFiles(self.annotations_folder, ['.txt'])

        # 3. get all the models
        self.models_folder = os.path.join(self.scene_folder, 'models')
        self.model_name_list = getFiles(self.models_folder, ['.obj'])

    def __len__(self):
        pass

    def __getitem__(self):
        pass


class V3PReader:
    def __init__(self, scene_folder):
        self.scene_folder = scene_folder
        self.open()

    def open(self):
        pass

    def __len__(self):
        pass

    def __getitem__(self):
        pass



if __name__ == "__main__":
    dataset = V3PDataset(r'D:\ssj\gitlab\traffic-show\scenes')
    