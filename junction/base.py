from abc import ABCMeta, abstractmethod, abstractproperty


class ABCUIElement(metaclass=ABCMeta):
    min_width = abstractproperty()
    max_width = abstractproperty()
    min_height = abstractproperty()
    max_height = abstractproperty()

    @abstractmethod
    def draw(self, width, height):
        pass
