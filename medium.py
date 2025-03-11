from item_draggable import Item
import pygame
import numpy as np


class Medium(Item):
    def __init__(self, pos, size, id, rot, n):
        super().__init__(pos, size, id)
        self._pos = pos
        self._size = size
        self._id = id
        self._refractive_index = n
        self._rotation = rot

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

    def get_centre(self):
        centre = self.get_pos()
        offset = [x / 2 for x in self.get_size()]
        centre[0] += offset[0]
        centre[1] -= offset[0]
        return centre

    def get_rotated(self):
        p = self.get_pos()
        s = self.get_size()
        r = self.get_rot()
        c = self.get_centre()
        verts = [
            (p[0], p[1]),
            (p[0] + s[0], p[1]),
            (p[0], p[1] - s[1]),
            (p[0] + s[0], p[1] - s[1]),
        ]
        verts = [(x - c[0], y - c[1]) for (x, y) in verts]
        mat = np.matrix([np.cos(r), -np.sin(r), np.sin(r), np.cos(r)])
        for coord in verts:
            coord @ mat
            #
        return verts

    def set_rot(self, rot):
        self._rotation = rot

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

    def get_rot(self):
        return self._rotation
