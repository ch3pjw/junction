from abc import ABCMeta, abstractmethod, abstractproperty


class ABCUIElement(metaclass=ABCMeta):
    min_width = abstractproperty()
    max_width = abstractproperty()
    min_height = abstractproperty()
    max_height = abstractproperty()

    @abstractmethod
    def draw(self, width, height):
        pass


class ABCContainerElement(ABCUIElement):
    def __init__(self, elements):
        self._content = []
        for element in elements:
            self.add_element(element)

    def __iter__(self):
        return iter(self._content)

    def add_element(self, element):
        self._content.append(element)

    def remove_element(self, element):
        self._content.remove(element)
