from abc import ABC
from abc import abstractmethod


class BaseImageProvider(ABC):

    @abstractmethod
    def generate_outfit_images(self, image_path, styling_plan):
        pass