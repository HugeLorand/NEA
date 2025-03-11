from item_draggable import Item
import pygame


class Medium(Item):
    def __init__(self, pos, size, id, n):
        super().__init__(pos, size, id)
        self._pos = pos
        self._size = size
        self._id = id
        self._refractive_index = n

    def get_pos(self, option=None):
        if option == "x":
            return self._pos[0]
        elif option == "y":
            return self._pos[1]
        else:
            return self._pos

    def get_size(self, option=None):
        if option == "x":
            return self._size[0]
        elif option == "y":
            return self._size[1]
        else:
            return self._size

    def set_pos(self, pos):
        self._pos = pos

    def set_size(self, size):
        self._size = size

    def get_refractive_index(self):
        return self._refractive_index

    def set_refractive_index(self, n):
        self._refractive_index = n

    def get_id(self):
        return self._id

    def get_rect(self):
        return pygame.Rect(self.get_pos(), self.get_size())
